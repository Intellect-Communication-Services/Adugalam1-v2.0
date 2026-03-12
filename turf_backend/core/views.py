import random
from datetime import timedelta,datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from math import radians, cos, sin, asin, sqrt
from django.db.models import F
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

import razorpay
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from .utils.email_service import send_email_otp,generate_otp
from core.utils.whatsapp_service import send_whatsapp

from django.contrib.auth import get_user_model
User = get_user_model()

from core.serializers import SlotSerializer, TurfSerializer,BookingListSerializer,VendorTurfCreateSerializer,AdminTurfCreateSerializer
from core.models import (
    AppUser,
    UserManager,
    EmailOTP,
    Cart,
    Booking,
    Payment,
    Turf,
    Ground,
    Slot, 
    AdminUser,
    Game,
    PeakHour,
)

@api_view(['GET'])
def home(request):
    return Response({
        "message": "Home API working",
        "status": "ok"
    })


@api_view(['POST'])
def send_email_otp_view(request):
    email = request.data.get("email")

    if AppUser.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    otp = generate_otp()

    EmailOTP.objects.update_or_create(
        email=email,
        defaults={"otp": otp, "is_verified": False}
    )

    send_email_otp(email, otp)

    return Response({"message": "OTP sent to email"})


#  VERIFY OTP
@api_view(['POST'])
def verify_email_otp_view(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    if not email or not otp:
        return Response({"error": "Email and OTP required"}, status=400)

    try:
        record = EmailOTP.objects.get(
            email=email,
            otp=otp,
            is_verified=False   # 🔥 IMPORTANT FIX
        )

        if record.is_expired():
            record.delete()
            return Response({"error": "OTP expired"}, status=400)

        record.is_verified = True
        record.save()

        return Response({"message": "OTP verified"})

    except EmailOTP.DoesNotExist:
        return Response({"error": "Invalid OTP"}, status=400)


#  CREATE ACCOUNT
@api_view(['POST'])
def create_account_view(request):
    name = request.data.get("name")
    email = request.data.get("email")
    mobile = request.data.get("mobile")
    password = request.data.get("password")
    confirm_password = request.data.get("confirm_password")

    #  Basic validation
    if not all([name, email, mobile, password, confirm_password]):
        return Response({"error": "All fields are required"}, status=400)

    #  Password match check
    if password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)

    #  OTP verification check
    otp_record = EmailOTP.objects.filter(email=email, is_verified=True).first()
    if not otp_record:
        return Response({"error": "OTP not verified"}, status=400)

    #  Create user
    user = AppUser.objects.create_user(
        email=email,
        password=password,
        name=name,
        mobile=mobile,
        is_verified=True
    )

    #  Cleanup OTP
    otp_record.delete()

    return Response({"message": "Account created successfully"})


#  LOGIN
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(request, email=email, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile
        }
    })

@api_view(['POST'])
def send_reset_otp(request):
    email = request.data.get('email')

    if not AppUser.objects.filter(email=email).exists():
        return Response({"error": "User not found"}, status=404)

    EmailOTP.objects.filter(email=email).delete()  # clear old OTPs

    otp = generate_otp()
    EmailOTP.objects.create(email=email, otp=otp, is_verified=False)

    send_email_otp(email, otp)

    return Response({"message": "Reset OTP sent"})

@api_view(['GET'])
def list_turfs(request):
    date_str = request.GET.get('date')
    
    # Filter: only show turfs from APPROVED vendors (or no vendor)
    qs = Turf.objects.select_related("owner", "vendor").prefetch_related(
        "banners", "gallery", "slot_items"
    ).filter(
        is_approved=True
    ).exclude(
        vendor__status="Inactive"  # Exclude turfs from inactive vendors
    ).order_by("-id")

    data = []

    for t in qs:
        available_slots = []

        # ✅ NEW SLOTS (SHOW ALL 24 HOURS — DO NOT FILTER)
        if hasattr(t, 'slot_items') and t.slot_items.exists():

            # 🔥 IMPORTANT CHANGE: removed filter(is_available=True)
            slots_qs = t.slot_items.all().order_by("start_time")

            for slot in slots_qs:
                available_slots.append({
                    "id": slot.id,
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "end_time": slot.end_time.strftime("%H:%M"),
                    "time_display": f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}",
                    "price_display": f"₹{slot.price}",
                    "price": slot.price,
                    "is_available": slot.is_available  # frontend will grey if False
                })

        else:
            # Legacy JSON fallback
            for slot in t.slots or []:
                available_slots.append({
                    "id": slot.get("id"),
                    "start_time": slot.get("start_time", ""),
                    "end_time": slot.get("end_time", ""),
                    "time_display": slot.get("slot_display", ""),
                    "price": slot.get("price", t.price_per_hour),
                    "price_display": f"₹{slot.get('price', t.price_per_hour)}",
                    "is_available": not slot.get("is_booked", False)
                })

        data.append({
            "id": t.id,
            "name": t.name,
            "location": t.location,
            "latitude": t.latitude,
            "longitude": t.longitude,
            "price_per_hour": t.price_per_hour,
            "description": t.description or "",
            "games": t.games or [],
            "amenities": t.amenities or [],
            "features": t.features or [],
            
            "banner_images": [img.image.url for img in t.banners.all()],
            "gallery_images": [img.image.url for img in t.gallery.all()],
            "slots": available_slots,
            
            "vendor": {
                "vendor_id": getattr(t.vendor, 'vendor_id', None) if t.vendor else None,
                "venuename": getattr(t.vendor, 'venuename', None) if t.vendor else None,
            },
            
            "owner": {
                "id": t.owner.id if t.owner else None,
                "username": t.owner.name if t.owner else None,
                "email": t.owner.email if t.owner else None,
            } if t.owner else {"id": None, "username": None, "email": None},
            
            "is_approved": t.is_approved,
        })

    return Response(data)

@api_view(['GET'])
def popular_turfs(request):

    qs = Turf.objects.filter(
        is_approved=True,
        is_popular=True
    ).exclude(
        vendor__status="Inactive"  # Exclude turfs from inactive vendors
    ).order_by("priority")

    data = []

    for t in qs:

        data.append({
            "id": t.id,
            "name": t.name,
            "location": t.location,
            "price_per_hour": t.price_per_hour,
            "games": t.games,  # ADD THIS
            "banner_images": [img.image.url for img in t.banners.all()],
        })

    return Response(data)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Turf



@api_view(['GET'])
def turf_slots(request):
    turf_id = request.GET.get("turf_id")
    date = request.GET.get("date")

    if not turf_id:
        return Response({"error": "turf_id required"}, status=400)

    slots = Slot.objects.filter(turf_id=turf_id).order_by("start_time")

    data = []

    for slot in slots:
        data.append({
            "id": slot.id,
            "start_time": slot.start_time.strftime("%H:%M"),
            "end_time": slot.end_time.strftime("%H:%M"),
            "time_display": f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}",
            "price": slot.price,
            "is_available": slot.is_available   # 🔥 IMPORTANT
        })

    return Response(data)

@api_view(['GET'])
def turf_details(request, turf_id):

    try:
        turf = Turf.objects.get(id=turf_id)
    except Turf.DoesNotExist:
        return Response({"error": "Turf not found"}, status=404)

    return Response({
        "id": turf.id,
        "name": turf.name,
        "location": turf.location,
        "price_per_hour": turf.price_per_hour,

        # ✅ ADD IMAGES
        "banner_images": [
            request.build_absolute_uri(img.image.url)
            for img in turf.banners.all()
        ],

        "gallery_images": [
            request.build_absolute_uri(img.image.url)
            for img in turf.gallery.all()
        ],
    })


@api_view(['GET'])
def ground_availability(request):
    turf_id=request.query_params.get('turf_id')
    game_type=request.query_params.get('game')
    if not turf_id or not game_type:
        return Response({"error": "turf_id and game required"}, status=400)
    grounds = Ground.objects.filter(turf_id=turf_id, game_type=game_type)
    data =[]
    for ground in grounds:
        slots = Slot.objects.filter(ground=ground,is_booked=False).values()

        data.append({
            "ground_id": ground.id,
            "ground_name": ground.name,
            "game": ground.game_type,
            "slots": list(slots)
        })

    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):

    turf_id = request.data.get("turf_id")
    date = request.data.get("date")
    slot_ids = request.data.get("slot_ids", [])

    if not turf_id or not date or not slot_ids:
        return Response({"error": "Missing fields"}, status=400)

    carts = []

    for slot_id in slot_ids:
        cart = Cart.objects.create(
            user=request.user,
            turf_id=turf_id,
            date=date,
            slot_id=slot_id
        )
        carts.append(cart.id)

    return Response({
        "message": "Added to cart",
        "cart_ids": carts
    })
from django.db import transaction
from django.db import transaction
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_booking(request):
    turf_id = request.data.get("turf_id")
    game_id = request.data.get("game_id")
    slot_ids = request.data.get("slot_ids", [])
    date = request.data.get("date")

    if not all([turf_id, slot_ids, date]):
        return Response({"error": "Missing fields"}, status=400)

    with transaction.atomic():

        slots = Slot.objects.select_for_update().filter(
            id__in=slot_ids,
            turf_id=turf_id,
            is_available=True
        )

        if slots.count() != len(slot_ids):
            return Response(
                {"error": "Some slots already booked"},
                status=400
            )

        # ✅ 1️⃣ ORIGINAL AMOUNT
        original_amount = sum(slot.price for slot in slots)

        # ✅ 2️⃣ 30% ADVANCE
        advance_amount = Decimal(original_amount) * Decimal("0.30")

        # ✅ 3️⃣ SERVICE CHARGE
        service_charge = Decimal("20.00")

        # ✅ 4️⃣ TOTAL PAYABLE (Advance + Service)
        total_payable = advance_amount + service_charge

        # lock slots
        slots.update(is_available=False)

        # create booking
        booking = Booking.objects.create(
            user=request.user,
            turf_id=turf_id,
            game_id=game_id,
            date=date,
            original_amount=original_amount,
            advance_amount=advance_amount,
            service_charge=service_charge,
            total_payable=total_payable,
            status="PENDING"
        )

        booking.slots.set(slots)

    return Response({
        "success": True,
        "booking_id": booking.id,
        "original_amount": original_amount,
        "advance_amount": advance_amount,
        "service_charge": service_charge,
        "total_payable": total_payable
    }, status=201)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, booking_id):

    try:
        booking = Booking.objects.prefetch_related("slots").get(
            id=booking_id,
            user=request.user
        )
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)

    # Return all pricing fields correctly
    return Response({
        "id": booking.id,
        "turf_name": booking.turf.name,
        "date": booking.date,
        "status": booking.status,
        "original_amount": booking.original_amount,
        "advance_amount": booking.advance_amount,
        "service_charge": booking.service_charge,
        "total_price": booking.total_payable,  # ✅ Use total_payable (advance + service)
        "slots": [
            {
                "time_display": f"{s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}",
                "price": s.price
            }
            for s in booking.slots.all()
        ],
    })
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_order(request):
    try:
        booking_id = request.data.get("booking_id")
        amount = request.data.get("amount")

        if not booking_id or not amount:
            return Response(
                {"error": "Booking ID and amount required"},
                status=400
            )

        booking = Booking.objects.get(
            id=booking_id,
            user=request.user
        )

        # ❌ Prevent duplicate successful payment
        if hasattr(booking, "payment") and booking.payment.status == "SUCCESS":
            return Response(
                {"error": "Payment already completed"},
                status=400
            )

        # 🔹 Razorpay client
        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))

        # 🔹 Create Razorpay order
        razorpay_order = client.order.create({
            "amount": amount,   # already in paise
            "currency": "INR",
            "payment_capture": "1"
        })

        # 🔹 Create or Update Payment (safe for OneToOne)
        payment, created = Payment.objects.update_or_create(
            booking=booking,
            defaults={
                "user": request.user,
                "razorpay_order_id": razorpay_order["id"],
                "amount": amount,
                "status": "PENDING"
            }
        )

        return Response({
            "order_id": razorpay_order["id"],
            "amount": amount
        })

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)

    except Exception as e:
        print("Payment Order Error:", str(e))
        return Response({"error": "Something went wrong"}, status=500)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):

    booking_id = request.data.get("booking_id")
    payment_id = request.data.get("payment_id")

    booking = Booking.objects.get(
        id=booking_id,
        user=request.user
    )

    payment = Payment.objects.get(booking=booking)

    payment.razorpay_payment_id = payment_id
    payment.amount = int(booking.total_payable * 100)  # ✅ FIX
    payment.status = "SUCCESS"
    payment.save()

    booking.status = "CONFIRMED"
    booking.vendor_status = "ACTIVE"
    booking.save()
    send_whatsapp(
    booking.user.mobile,
    f"""
Booking Confirmed

Turf: {booking.turf.name}
Date: {booking.date}

Enjoy your game!
"""
)

    return Response({"success": True})

@api_view(["GET"])
def nearby_turfs(request):
    lat = request.query_params.get("lat")
    lng = request.query_params.get("lng")
    radius_km = float(request.query_params.get("radius", 10))

    if not lat or not lng:
        return Response({"error": "lat and lng required"}, status=400)

    lat = float(lat)
    lng = float(lng)

    turfs = Turf.objects.filter(is_approved=True)

    results = []
    for turf in turfs:
        if turf.latitude is None or turf.longitude is None:
            continue

        # Haversine distance
        dlat = radians(turf.latitude - lat)
        dlon = radians(turf.longitude - lng)
        a = sin(dlat/2)**2 + cos(radians(lat)) * cos(radians(turf.latitude)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance = 6371 * c  # km

        if distance <= radius_km:
            results.append({
                "id": turf.id,
                "name": turf.name,
                "location": turf.location,
                "distance_km": round(distance, 2),
            })

    return Response(results)

@api_view(['GET'])
def turf_games(request, turf_id):
    games=Ground.objects.filter(turf_id=turf_id)\
        .values("game_type").distinct()
    return Response(list(games))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookings(request):

    bookings = Booking.objects.filter(user=request.user).select_related(
        "turf", "slot", "game"
    )

    data = []

    for b in bookings:
        data.append({
            "id": b.id,
            "turf_name": b.turf.name,
            "game": b.game.game_name,
            "date": b.date,
            "start_time": b.slot.start_time,
            "end_time": b.slot.end_time,
            "status": b.status,
        })

    return Response(data)



from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import AppUser, EmailOTP


@api_view(['POST'])
def reset_password(request):
    email = request.data.get('email')
    new_password = request.data.get('password')
    otp = request.data.get('otp')

    if not all([email, new_password, otp]):
        return Response({"error": "Missing fields"}, status=400)

    # 1️⃣ Verify OTP
    try:
        otp_obj = EmailOTP.objects.get(
            email=email,
            otp=otp,
            is_verified=True
        )
    except EmailOTP.DoesNotExist:
        return Response({"error": "Invalid or unverified OTP"}, status=400)

    # 2️⃣ Get user
    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    # 3️⃣ Reset password
    user.password = make_password(new_password)
    user.save()

    # 4️⃣ Invalidate OTP
    otp_obj.delete()

    return Response({"message": "Password reset successful"})

class TurfListView(ListAPIView):
    queryset = Turf.objects.all()
    serializer_class = TurfSerializer

    def get_serializer_context(self):
        context= super().get_serializer_context()
        context.update({"request": self.request})
        return context

# -------------------Admin Views ---------------------------#
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random

@api_view(['POST'])
def admin_send_otp(request):
    email = request.data.get('email')
    role = "ADMIN"

    if not email:
        return Response({"error": "Email required"}, status=400)

    # Prevent duplicate admin
    if AdminUser.objects.filter(email=email).exists():
        return Response({"error": "Admin already exists"}, status=400)

    # Generate OTP
    otp = str(random.randint(100000, 999999))

    # Delete old OTPs
    EmailOTP.objects.filter(email=email).delete()

    # Save OTP
    EmailOTP.objects.create(email=email, otp=otp)

    # Send Email
    send_mail(
        subject="Admin OTP Verification",
        message=f"Your Admin OTP is: {otp}\nValid for 5 minutes.",
        from_email="noreply@adugalam.com",
        recipient_list=[email],
        fail_silently=False
    )

    return Response({"message": "OTP sent to admin email"})


from django.utils import timezone
from django.contrib.auth.hashers import make_password

@api_view(['POST'])
def admin_verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    password = request.data.get('password')
    name = request.data.get('name')
    phone = request.data.get('phone')

    if not all([email, otp, password]):
        return Response({"error": "Missing fields"}, status=400)

    otp_obj = EmailOTP.objects.filter(email=email, otp=otp).first()

    if not otp_obj:
        return Response({"error": "Invalid OTP"}, status=400)

    # Expiry check
    if otp_obj.is_expired():
        otp_obj.delete()
        return Response({"error": "OTP expired"}, status=400)

    # Duplicate admin check
    if AdminUser.objects.filter(email=email).exists():
        return Response({"error": "Admin already exists"}, status=400)

    # Create Admin
    AdminUser.objects.create(
        name=name,
        email=email,
        phone=phone,
        password=make_password(password)
    )

    otp_obj.delete()

    return Response({"message": "Admin account created"})

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

@api_view(['POST'])
def admin_login(request):
    password = request.data.get("password")
    email = request.data.get("email")
    phone = request.data.get("phone")

    try:
        if email:
            admin = AdminUser.objects.get(email=email)
        elif phone:
            admin = AdminUser.objects.get(phone=phone)
        else:
            return Response({"error": "Email or phone required"}, status=400)
    except AdminUser.DoesNotExist:
        return Response({"error": "Invalid credentials"}, status=400)

    if not check_password(password, admin.password):
        return Response({"error": "Invalid credentials"}, status=400)

    # 🔑 Map AdminUser → AppUser
    User = get_user_model()

    user, created = User.objects.get_or_create(
        email=admin.email,
        defaults={
            "name": admin.name,
            "mobile": admin.phone,
            "role": "ADMIN",
            "is_staff": True,
            "is_superuser": True,
            "is_verified": True
        }
    )

    # If already exists, force admin role
    user.role = "ADMIN"
    user.is_staff = True
    user.is_superuser = True
    user.save()

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "role": user.role,
        "message": "Admin login successful"
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def admin_dashboard_main(request):
    try:
        from core.models import Turf, Booking, Payment, Vendor
        from django.contrib.auth import get_user_model
        from django.db.models.functions import TruncDate
        from django.db.models import Count, Sum
        from django.utils import timezone
        
        User = get_user_model()
        
        total_users = User.objects.count()
        total_vendors = Vendor.objects.count()
        total_turfs = Turf.objects.count()
        total_bookings = Booking.objects.count()
        today = timezone.localdate()
        start = today - timezone.timedelta(days=6)
        
        today_bookings = Booking.objects.filter(created_at__date=today).count()
        
        today_new_users = 0
        if hasattr(User, 'date_joined'):
            today_new_users = User.objects.filter(date_joined__date=today).count()
        elif hasattr(User, 'created_at'):
            today_new_users = User.objects.filter(created_at__date=today).count()
            
        today_new_vendors = Vendor.objects.filter(created_at__date=today).count() if hasattr(Vendor, 'created_at') else 0
        today_revenue_paise = (
            Payment.objects.filter(status="SUCCESS", created_at__date=today).aggregate(s=Sum("amount"))["s"] or 0
        )
        days = [start + timezone.timedelta(days=i) for i in range(7)]
        
        booking_counts_qs = Booking.objects.filter(created_at__date__gte=start, created_at__date__lte=today).annotate(d=TruncDate('created_at')).values("d").annotate(c=Count("id"))
        booking_counts = { row["d"]: row["c"] for row in booking_counts_qs }
        revenue_qs = Payment.objects.filter(status="SUCCESS", created_at__date__gte=start, created_at__date__lte=today).annotate(d=TruncDate('created_at')).values("d").annotate(s=Sum("amount"))
        revenue = { row["d"]: row["s"] for row in revenue_qs }
        weekly_data = []
        for d in days:
            weekly_data.append({
                "day": d.strftime("%a"),
                "bookings": int(booking_counts.get(d, 0) or 0),
                "revenue": int(revenue.get(d, 0) or 0) / 100
            })
            
        payload = {
            "success": True,
            "stats": {
                "users": total_users,
                "vendors": total_vendors,
                "turfs": total_turfs,
                "bookings": total_bookings,
            },
            "today": {
                "bookings": today_bookings,
                "revenue": float(today_revenue_paise / 100),
                "users": today_new_users,
                "vendors": today_new_vendors,
            },
            "weekly": weekly_data
        }
        return Response(payload)
    except Exception as e:
        import traceback
        return Response({"success": False, "error": str(e), "traceback": traceback.format_exc()})


@staff_member_required
def dashboard_weekly(request):
    """Returns last 7 days booking counts and revenue totals for chart."""
    today = timezone.localdate()
    start = today - timezone.timedelta(days=6)
    days = [start + timezone.timedelta(days=i) for i in range(7)]

    booking_counts = {
        row["d"]: row["c"]
        for row in Booking.objects.filter(created_at__date__gte=start, created_at__date__lte=today)
        .extra(select={"d": "date(created_at)"})
        .values("d")
        .annotate(c=Count("id"))
    }

    revenue = {
        row["d"]: row["s"]
        for row in Payment.objects.filter(
            status="SUCCESS", created_at__date__gte=start, created_at__date__lte=today
        )
        .extra(select={"d": "date(created_at)"})
        .values("d")
        .annotate(s=Sum("amount"))
    }

    payload = {
        "labels": [d.strftime("%a") for d in days],
        "bookings": [int(booking_counts.get(d, 0)) for d in days],
        "revenue_paise": [int(revenue.get(d, 0) or 0) for d in days],
    }
    return JsonResponse(payload)


@staff_member_required
def users_list(request):
    qs = User.objects.all().order_by("-date_joined")
    data = [
        {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "is_active": u.is_active,
            "date_joined": u.date_joined,
        }
        for u in qs
    ]
    return JsonResponse({"results": data})


@staff_member_required
def user_toggle_active(request, user_id: int):
    if request.method not in ("POST", "PATCH"):
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found"}, status=404)
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    return JsonResponse({"id": u.id, "is_active": u.is_active})



@api_view(["GET"])
@permission_classes([AllowAny])
def turfs_list(request):
    date_str = request.GET.get('date')
    
    # Filter: only show turfs from APPROVED vendors (or no vendor)
    qs = Turf.objects.select_related("owner", "vendor").prefetch_related(
        "banners", "gallery", "slot_items"
    ).filter(
        is_approved=True
    ).exclude(
        vendor__status="Inactive"  # Exclude turfs from inactive vendors
    ).order_by("-id")

    data = []
    for t in qs:
        available_slots = []
        
        # NEW SLOTS ✅
        if hasattr(t, 'slot_items') and t.slot_items.exists():
            slots_qs = t.slot_items.filter(is_available=True)
            
            # Date filter (if date field added later)
            if date_str:
                # slots_qs = slots_qs.filter(date=date_str)  # Add date field to Slot
                pass
                
            for slot in slots_qs:
                available_slots.append({
                    "id": slot.id,
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "end_time": slot.end_time.strftime("%H:%M"),
                    "time_display": f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}",
                    "price_display": f"₹{slot.price}",
                    "price": slot.price,
                    "is_available": slot.is_available
                })
        else:
            # Legacy JSON fallback
            for slot in t.slots or []:
                if not slot.get("is_booked", False):
                    available_slots.append({
                        "id": slot.get("id"),
                        "start_time": slot.get("start_time", ""),
                        "end_time": slot.get("end_time", ""),
                        "time_display": slot.get("slot_display", ""),
                        "price": slot.get("price", t.price_per_hour),
                        "price_display": f"₹{slot.get('price', t.price_per_hour)}",
                        "is_available": True
                    })

        data.append({
            "id": t.id,
            "name": t.name,
            "location": t.location,
            "latitude": t.latitude,
            "longitude": t.longitude,
            "price_per_hour": t.price_per_hour,
            "description": t.description or "",
            "games": t.games or [],
            "amenities": t.amenities or [],
            "features": t.features or [],

            "banner_images": [img.image.url for img in t.banners.all()],
            "gallery_images": [img.image.url for img in t.gallery.all()],
            "slots": available_slots,  # ✅ Dynamic slots ready

            # ✅ SAFE VENDOR ACCESS
            "vendor": {
                "vendor_id": getattr(t.vendor, 'vendor_id', None) if t.vendor else None,
                "venuename": getattr(t.vendor, 'venuename', None) if t.vendor else None,
            },
            
            # ✅ SAFE OWNER ACCESS
            "owner": {
                "id": t.owner.id if t.owner else None,
                "username": t.owner.name if t.owner else None,
                "email": t.owner.email if t.owner else None,
            } if t.owner else {"id": None, "username": None, "email": None},
            
            "is_approved": t.is_approved,
        })

    return Response({"results": data})

@api_view(['GET'])
def turf_detail(request, turf_id):
    """Single turf with all slots"""
    try:
        turf = Turf.objects.get(id=turf_id, is_approved=True)
        slots = Slot.objects.filter(turf=turf).order_by('start_time')
        
        return Response({
            'id': turf.id,
            'name': turf.name,
            'location': turf.location,
            'price_per_hour': turf.price_per_hour,
            'description': turf.description,
            'games': [
                {
                   "id": g.id,
                   "game_name": g.game_name,
                   "price": g.price
                }
                for g in turf.game_set.all()
            ],
            'amenities': turf.amenities,
            'features': turf.features,
            'slots': SlotSerializer(slots, many=True).data,
            'banners': [banner.image.url for banner in turf.banners.all()],
            'gallery': [img.image.url for img in turf.gallery.all()]
        })
    except Turf.DoesNotExist:
        return Response({"error": "Turf not found"}, status=404)
    
    
@staff_member_required
def bookings_list(request):
    qs = Booking.objects.select_related("user", "cart", "cart__turf", "cart__ground", "cart__slot").order_by(
        "-created_at"
    )
    data = []
    for b in qs:
        data.append(
            {
                "id": b.id,
                "status": b.status,
                "created_at": b.created_at,
                "user": {
                    "id": b.user.id,
                    "username": b.user.username,
                    "email": b.user.email,
                },
                "turf": {
                    "id": b.cart.turf_id,
                    "name": getattr(b.cart.turf, "name", None),
                },
                "ground": {
                    "id": b.cart.ground_id,
                    "name": getattr(b.cart.ground, "name", None),
                },
                "date": b.cart.date,
                "slot": {
                    "id": b.cart.slot_id,
                    "start_time": getattr(b.cart.slot, "start_time", None),
                    "end_time": getattr(b.cart.slot, "end_time", None),
                },
                "amount_paise": getattr(b.cart.turf, "price_per_hour", None),
            }
        )
    return JsonResponse({"results": data})


@staff_member_required
def booking_cancel(request, booking_id: int):
    if request.method not in ("POST", "PATCH"):
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        b = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({"detail": "Booking not found"}, status=404)
    b.status = "CANCELLED"
    b.save(update_fields=["status"])
    return JsonResponse({"id": b.id, "status": b.status})


@staff_member_required
def payments_list(request):
    qs = Payment.objects.select_related("user", "booking").order_by("-created_at")
    data = [
        {
            "id": p.id,
            "booking_id": p.booking_id,
            "user": {
                "id": p.user.id,
                "username": p.user.username,
                "email": p.user.email,
            },
            "razorpay_order_id": p.razorpay_order_id,
            "razorpay_payment_id": p.razorpay_payment_id,
            "amount": p.amount,
            "status": p.status,
            "created_at": p.created_at,
        }
        for p in qs
    ]
    return JsonResponse({"results": data})


# --- Vendor endpoints (stub) ---
# Your backend doesn't include a Vendor model yet.
# These endpoints exist so your Admin React flow won't break.


@staff_member_required
def vendors_list(request):
    return JsonResponse({"results": []})


@staff_member_required
def vendor_approve(request, user_id: int):
    return JsonResponse({"detail": "Vendor module not implemented in backend"}, status=501)


@staff_member_required
def vendor_reject(request, user_id: int):
    return JsonResponse({"detail": "Vendor module not implemented in backend"}, status=501)

@staff_member_required
def turfs_approve(request, turf_id):
    if request.method not in ("POST", "PATCH"):
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        turf = Turf.objects.get(id=turf_id)
    except Turf.DoesNotExist:
        return JsonResponse({"detail": "Turf not found"}, status=404)

    turf.is_approved = True
    turf.save(update_fields=["is_approved"])

    return JsonResponse({
        "id": turf.id,
        "is_approved": True,
        "message": "Turf approved"
    })


@staff_member_required
def turfs_reject(request, turf_id):
    if request.method not in ("POST", "PATCH"):
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        turf = Turf.objects.get(id=turf_id)
    except Turf.DoesNotExist:
        return JsonResponse({"detail": "Turf not found"}, status=404)

    turf.is_approved = False
    turf.save(update_fields=["is_approved"])

    return JsonResponse({
        "id": turf.id,
        "is_approved": False,
        "message": "Turf rejected"
    })

# -----------------Vendor Views --------------------#

# --------- Helpers

def _ensure_vendor(user) -> bool:
    # Minimal vendor rule: must be authenticated. You can tighten this later.
    return user and user.is_authenticated


# --------- Vendor Dashboard

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_dashboard(request):
    """Return stats for Vendor/Dashboard.jsx.

    Notes:
    - Your frontend currently uses dummy data; this endpoint gives real data
      based on turfs owned by the logged-in user.
    """

    if not _ensure_vendor(request.user):
        return Response({"detail": "Unauthorized"}, status=401)

    owner = request.user
    owned_turfs = Turf.objects.filter(owner=owner)
    turf_ids = list(owned_turfs.values_list("id", flat=True))

    # Bookings for owned turfs via Cart -> Turf
    bookings_qs = Booking.objects.filter(cart__turf_id__in=turf_ids)

    today = now().date()
    todays = bookings_qs.filter(cart__date=today).count()
    upcoming = bookings_qs.filter(cart__date__gt=today).count()

    # Earnings: sum successful payments for those bookings
    earnings = (
        Payment.objects.filter(booking__in=bookings_qs, status="SUCCESS")
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    pending_approvals = bookings_qs.filter(vendor_status__iexact="PENDING").count()

    data = {
        "stats": [
            {"title": "Total Turfs Owned", "value": owned_turfs.count(), "icon": "🏠"},
            {"title": "Today’s Bookings", "value": todays, "icon": "📅"},
            {"title": "Upcoming Bookings", "value": upcoming, "icon": "🗓️"},
            # amounts stored in paise; convert to rupees for display
            {"title": "Monthly Earnings", "value": round(earnings / 100, 2), "icon": "💲"},
            {"title": "Pending Approvals", "value": pending_approvals, "icon": "⏳"},
        ],
        # Keep these for UI compatibility (frontend shows these blocks)
        "coaches": [],
        "reviews": [],
    }

    return Response(data)


# --------- Turfs

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_list_turfs(request):
    turfs = Turf.objects.filter(owner=request.user)
    return Response(TurfSerializer(turfs, many=True).data)


from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def vendor_add_turf(request):
    """Enhanced vendor turf creation with full features including images, games, slots"""
    ser = VendorTurfCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    payload = ser.validated_data

    turf_count = payload.get("turfCount") or 1

    # -------------------------
    # ✅ GET TURF NAME (support both name and turfName)
    # -------------------------
    turf_name = payload.get("turfName") or payload.get("name") or "Unnamed Turf"

    # -------------------------
    # ✅ GET VENDOR (if vendorId provided)
    # -------------------------
    vendor = None
    vendor_id = payload.get("vendorId")
    if vendor_id:
        try:
            vendor = Vendor.objects.get(vendor_id=vendor_id)
        except Vendor.DoesNotExist:
            pass

    # -------------------------
    # ✅ CREATE TURF (as per your requested format)
    # -------------------------
    turf = Turf.objects.create(
        name=turf_name,
        location=payload["location"],
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        price_per_hour=payload["price"],
        description=payload.get("description", ""),
        amenities=payload.get("amenities", []),
        features=payload.get("features", []),
        vendor=vendor,
        vendor_code=vendor.vendor_id if vendor else None,
        owner=request.user,
        is_approved=True
    )

    # -------------------------
    # ✅ CREATE GAMES
    # -------------------------
    games = payload.get("games", [])
    if isinstance(games, str):
        try:
            games = json.loads(games)
        except:
            games = []

    for game_name in games:
        Game.objects.create(
            turf=turf,
            game_name=game_name,
            price=turf.price_per_hour
        )

    # -------------------------
    # ✅ CREATE GROUNDS
    # -------------------------
    for i in range(1, turf_count + 1):
        Ground.objects.create(turf=turf, name=f"Ground {i}")

    # -------------------------
    # ✅ CREATE SLOTS
    # -------------------------
    slots = payload.get("slots", [])
    if isinstance(slots, str):
        try:
            slots = json.loads(slots)
        except:
            slots = []

    for s in slots:
        try:
            # ⭐ CONVERT STRING → TIME OBJECT
            start_time = datetime.strptime(s.get("from", ""), "%I:%M %p").time()
            end_time = datetime.strptime(s.get("to", ""), "%I:%M %p").time()
            
            Slot.objects.create(
                turf=turf,
                start_time=start_time,
                end_time=end_time,
                price=s.get("price", turf.price_per_hour),
                is_available=True
            )
        except Exception as e:
            print(f"Slot creation error: {e}")
            continue

    # -------------------------
    # ✅ SAVE BANNERS (from request.FILES)
    # -------------------------
    for img in request.FILES.getlist("banner_images"):
        TurfBanner.objects.create(
            turf=turf,
            image=img
        )

    # -------------------------
    # ✅ SAVE GALLERY (from request.FILES)
    # -------------------------
    for img in request.FILES.getlist("gallery_images"):
        TurfGallery.objects.create(
            turf=turf,
            image=img
        )

    return Response({
        "success": True,
        "turf_id": turf.id,
        "message": "Turf created successfully"
    })


# -------------------------
# ✅ CALCULATE DISTANCE HELPER FUNCTION
# -------------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    lon1, lat1, lon2, lat2 = map(
        radians,
        [lon1, lat1, lon2, lat2]
    )

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2

    c = 2 * asin(sqrt(a))

    r = 6371  # Radius of Earth in kilometers

    return c * r


# --------- Booking Management

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_booking_list(request):
    """Return bookings belonging to vendor-owned turfs."""
    turfs = Turf.objects.filter(owner=request.user)
    turf_ids = list(turfs.values_list("id", flat=True))
    qs = Booking.objects.select_related("user", "cart", "cart__turf", "cart__ground", "cart__slot").filter(
        cart__turf_id__in=turf_ids
    ).order_by("-created_at")

    data = BookingListSerializer(qs, many=True).data
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vendor_update_booking_status(request):
    """Used by Vendor/BookingManagement.jsx (placeholder).

    Accepts:
      { bookingId: "#BK101" or 123, status: "Approved"|"Rejected"|"Cancelled" }
    We map this to Booking.vendor_status and optionally Booking.status.
    """
    booking_id = request.data.get("bookingId")
    status_text = (request.data.get("status") or "").strip()

    if not booking_id or not status_text:
        return Response({"success": False, "error": "bookingId and status required"}, status=400)

    # bookingId may come as "#BK101" in UI dummy; try to parse digits
    if isinstance(booking_id, str) and booking_id.startswith("#"):
        digits = "".join([c for c in booking_id if c.isdigit()])
        booking_id = int(digits) if digits else None

    try:
        booking = Booking.objects.select_related("cart", "cart__turf").get(id=booking_id)
    except Exception:
        return Response({"success": False, "error": "Booking not found"}, status=404)

    # Ensure booking belongs to vendor
    if booking.cart.turf.owner_id != request.user.id:
        return Response({"success": False, "error": "Forbidden"}, status=403)

    normalized = status_text.upper()
    if normalized == "APPROVED":
        booking.vendor_status = "APPROVED"
        booking.status = "CONFIRMED"
    elif normalized == "REJECTED":
        booking.vendor_status = "REJECTED"
        booking.status = "CANCELLED"
    elif normalized == "CANCELLED":
        booking.vendor_status = "CANCELLED"
        booking.status = "CANCELLED"
    else:
        booking.vendor_status = status_text

    booking.save(update_fields=["vendor_status", "status"])
    return Response({"success": True})


# --------- Schedule Time (Slots)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_list_slots(request):
    """List slots for a ground (and vendor must own the turf)."""
    ground_id = request.query_params.get("ground_id")
    if not ground_id:
        return Response({"error": "ground_id required"}, status=400)

    try:
        ground = Ground.objects.select_related("turf").get(id=ground_id)
    except Ground.DoesNotExist:
        return Response({"error": "Ground not found"}, status=404)

    if ground.turf.owner_id != request.user.id:
        return Response({"error": "Forbidden"}, status=403)

    slots = Slot.objects.filter(ground=ground).order_by("start_time")
    return Response(
        [
            {
                "id": s.id,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "is_booked": s.is_booked,
            }
            for s in slots
        ]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vendor_create_slots(request):
    """Create slots for a ground.

    Expected payload:
      { ground_id: 1, slots: [{start_time: "06:00", end_time: "07:00"}, ...] }
    """
    ground_id = request.data.get("ground_id")
    slots = request.data.get("slots") or []

    if not ground_id or not isinstance(slots, list) or not slots:
        return Response({"success": False, "error": "ground_id and slots[] required"}, status=400)

    try:
        ground = Ground.objects.select_related("turf").get(id=ground_id)
    except Ground.DoesNotExist:
        return Response({"success": False, "error": "Ground not found"}, status=404)

    if ground.turf.owner_id != request.user.id:
        return Response({"success": False, "error": "Forbidden"}, status=403)

    created = 0
    for item in slots:
        st = item.get("start_time")
        et = item.get("end_time")
        if not st or not et:
            continue
        Slot.objects.create(ground=ground, start_time=st, end_time=et)
        created += 1

    return Response({"success": True, "created": created})


# --------- Discount (placeholder – no Discount model in backend yet)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_list_discounts(request):
    """Placeholder: frontend has DiscountPage but backend has no Discount model.

    Returns empty list for now.
    """
    return Response([])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vendor_create_discount(request):
    """Placeholder endpoint so frontend can submit Deal Request."""
    return Response({"success": True})

# ----------------adminlaa vendor add panna vendiya model-----------------
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TurfBanner, TurfGallery, Vendor
from datetime import datetime
import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor


# ---------------- WHATSAPP FUNCTION ----------------
def send_whatsapp(phone, message):
    print("WHATSAPP FUNCTION CALLED") 
    url = "https://api.goinfinity.ai/api/v1/whatsapp/send"

    headers = {
        "Authorization": f"Bearer {settings.GOINFINITY_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "phone": phone,
        "message": message
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("WhatsApp Response:", response.text)
    except Exception as e:
        print("WhatsApp Error:", str(e))

@api_view(['POST'])
def create_vendor(request):
    try:
        data = request.data

        vendor = Vendor.objects.create(
            venuename=data.get("venuename"),
            ownername=data.get("ownername"),
            email=data.get("email"),
            phone=data.get("phone"),
            location=data.get("location"),
            address=data.get("address"),
            pincode=data.get("pincode"),
            totalturf=int(data.get("totalturf")),
            availablegames=data.get("availablegames", []),
            status="Approved"
        )

        # ✅ Send WhatsApp Message
        message = f"""
Hello {vendor.ownername},

Your Vendor account has been created successfully.

Vendor ID: {vendor.vendor_id}
Venue Name: {vendor.venuename}

Thank you for joining our platform.
"""

        send_whatsapp(vendor.phone, message)

        return Response({
            "message": "Vendor Created",
            "vendor_id": vendor.vendor_id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)
# ------------add turf page laa vendor id kuduta name varnu------------------------------
@api_view(['GET'])
def get_vendor(request, vendor_id):
    try:
        vendor = Vendor.objects.get(vendor_id=vendor_id)

        return Response({
            "id": vendor.id,
            "vendor_id": vendor.vendor_id,
            "venuename": vendor.venuename,
            "ownername": vendor.ownername,
            "phone": vendor.phone,
            "email": vendor.email,
            "location": vendor.location,
            "address": vendor.address,
            "pincode": vendor.pincode,
            "totalturf": vendor.totalturf,
            "availablegames": vendor.availablegames,
            "status": vendor.status,
        })

    except Vendor.DoesNotExist:
        return Response(
            {"error": "Vendor not found"},
            status=404
        )

# ------------- vendor list------------------
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Vendor
from django.forms.models import model_to_dict


@api_view(['GET'])
def vendor_list(request):
    vendors = Vendor.objects.all().order_by('-created_at')

    data = []
    for v in vendors:
        data.append({
            "id": v.id,
            "vendor_id": v.vendor_id,
            "venuename": v.venuename,
            "ownername": v.ownername,
            "phone": v.phone,
            "location": v.location,
            "totalturf": v.totalturf,
            "status": v.status,
        })

    return Response(data)
@api_view(['DELETE'])
def delete_vendor(request, id):
    try:
        vendor = Vendor.objects.get(vendor_id=id)
        vendor.delete()
        return Response({"message": "Deleted"})
    except Vendor.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    

@api_view(['PUT'])
def vendor_status_toggle(request, vendor_id):
    try:
        vendor = Vendor.objects.get(vendor_id=vendor_id)
        new_status = request.data.get("status")
        vendor.status = new_status
        vendor.save()
        
        # Also update all related turfs based on vendor status
        # When vendor is "Approved" or "Inactive", sync turf is_approved
        if new_status == "Approved":
            # Activate all turfs belonging to this vendor
            Turf.objects.filter(vendor=vendor).update(is_approved=True)
        elif new_status == "Inactive":
            # Deactivate all turfs belonging to this vendor
            Turf.objects.filter(vendor=vendor).update(is_approved=False)
        
        return Response({"message": "Status updated", "status": vendor.status})
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)


@api_view(['PUT'])
def update_vendor_by_code(request, vendor_id):
    """Update vendor details by vendor_id"""
    try:
        vendor = Vendor.objects.get(vendor_id=vendor_id)
        
        # Update fields if provided
        if request.data.get("venuename"):
            vendor.venuename = request.data.get("venuename")
        if request.data.get("ownername"):
            vendor.ownername = request.data.get("ownername")
        if request.data.get("phone"):
            vendor.phone = request.data.get("phone")
        if request.data.get("email"):
            vendor.email = request.data.get("email")
        if request.data.get("location"):
            vendor.location = request.data.get("location")
        if request.data.get("address"):
            vendor.address = request.data.get("address")
        if request.data.get("pincode"):
            vendor.pincode = request.data.get("pincode")
        if request.data.get("totalturf"):
            vendor.totalturf = request.data.get("totalturf")
            
        vendor.save()
        
        return Response({
            "message": "Vendor updated successfully",
            "vendor_id": vendor.vendor_id
        })
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


#------------------Admin Adding Turf through vendor id---------------------#
from datetime import datetime
import json
from rest_framework.parsers import MultiPartParser, FormParser


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def admin_add_turf(request):

    ser = AdminTurfCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    # -------------------------
    # ✅ GET VENDOR
    # -------------------------
    vendor = Vendor.objects.get(vendor_id=data["vendorId"])

    # -------------------------
    # ✅ CREATE TURF
    # -------------------------
    turf = Turf.objects.create(
    name=data["name"],
    location=data["location"],
    price_per_hour=data["price"],
    description=data.get("description", ""),
    amenities=data.get("amenities", []),
    features=data.get("features", []),
    vendor=vendor,
    vendor_code=vendor.vendor_id,
    owner=request.user,
    is_approved=True
)
    
    # -------------------------
    # ✅ CREATE GAMES (FIXED FOR YOUR FRONTEND)
    # -------------------------
    games = data.get("games", [])

    if isinstance(games, str):
     games = json.loads(games)

    for game_name in games:
     Game.objects.create(
        turf=turf,
        game_name=game_name,
        price=turf.price_per_hour   # use turf price
    )

    # -------------------------
    # ✅ CREATE SLOT ROWS (FIXED)
    # -------------------------
    slots = data.get("slots", [])

    # FormData sends string
    if isinstance(slots, str):
        slots = json.loads(slots)

    for s in slots:

        # ⭐ CONVERT STRING → TIME OBJECT
        start_time = datetime.strptime(
            s["from"], "%I:%M %p"
        ).time()

        end_time = datetime.strptime(
            s["to"], "%I:%M %p"
        ).time()

        Slot.objects.create(
            turf=turf,
            start_time=start_time,
            end_time=end_time,
            price=s["price"],
            is_available=True
        )

    # -------------------------
    # ✅ SAVE BANNERS
    # -------------------------
    for img in request.FILES.getlist("banner_images"):
        TurfBanner.objects.create(
            turf=turf,
            image=img
        )

    # -------------------------
    # ✅ SAVE GALLERY
    # -------------------------
    for img in request.FILES.getlist("gallery_images"):
        TurfGallery.objects.create(
            turf=turf,
            image=img
        )
        send_whatsapp(
    vendor.phone,
    f"""
New Turf Added Successfully

Turf Name: {turf.name}
Location: {turf.location}
"""
)

    return Response({
        "success": True,
        "turf_id": turf.id
    }, status=201)

@api_view(["PATCH"])
def update_turf_priority(request, turf_id):

    try:
        turf = Turf.objects.get(id=turf_id)
    except Turf.DoesNotExist:
        return Response({"error": "Turf not found"}, status=404)

    turf.is_popular = request.data.get("is_popular", turf.is_popular)
    turf.priority = request.data.get("priority", turf.priority)

    turf.save()

    return Response({"message": "Priority updated"})
@api_view(["POST"])
def book_slot(request):

    turf = Turf.objects.get(id=request.data["turf_id"])
    slot_id = request.data["slot_id"]

    slots = turf.slots

    for slot in slots:
        if slot["id"] == slot_id:
            if slot["is_booked"]:
                return Response({"error": "Already booked"}, status=400)

            slot["is_booked"] = True

    turf.slots = slots
    turf.save()

    return Response({"success": True})

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from .models import Slot


@api_view(["GET"])
def turf_slots(request):

    turf_id = request.query_params.get("turf_id")
    date_str = request.query_params.get("date")

    if not turf_id:
        return Response({"error": "turf_id required"}, status=400)

    # Get ALL slots (both available and booked) - removed is_available filter
    slots = Slot.objects.filter(turf_id=turf_id)

    selected_date = None

    # ✅ DATE FILTER
    if date_str:
        try:
            selected_date = datetime.strptime(
                date_str, "%Y-%m-%d"
            ).date()
        except ValueError:
            return Response({"error": "Invalid date"}, status=400)

    # ✅ HIDE PAST TIME
    today = timezone.localdate()

    if selected_date and selected_date == today:
        now_time = timezone.localtime().time()
        slots = slots.filter(start_time__gt=now_time)

    slots = slots.order_by("start_time")

    data = []

    # ✅ LOOP CORRECT
    for s in slots:

        price = s.price

        # ⭐ PEAK PRICE CHECK
        if selected_date:
            peak = PeakHour.objects.filter(
                turf_id=turf_id,
                slot=s,
                date=selected_date
            ).first()

            if peak:
                price = peak.peak_price

        data.append({
            "id": s.id,
            "start_time": s.start_time.strftime("%H:%M:%S"),
            "end_time": s.end_time.strftime("%H:%M:%S"),
            "time_display":
                f"{s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}",
            "price": price,
            "is_available": s.is_available,
        })

    # ✅ IMPORTANT RETURN
    return Response(data)
#-----------------------peak hours -----------------------#
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def vendor_set_peak_hour(request):

    turf_id = request.data.get("turf_id")
    game_id = request.data.get("game_id")
    slot_id = request.data.get("slot_id")
    date = request.data.get("date")
    peak_price = request.data.get("price")

    if not all([turf_id, game_id, slot_id, date, peak_price]):
        return Response({"error": "All fields required"}, status=400)

    try:
        turf = Turf.objects.get(id=turf_id, owner=request.user)
        slot = Slot.objects.get(id=slot_id, turf=turf)
        game = Game.objects.get(id=game_id, turf=turf)
    except:
        return Response({"error": "Invalid turf/game/slot"}, status=400)

    peak, created = PeakHour.objects.update_or_create(
        turf=turf,
        slot=slot,
        date=date,
        defaults={
            "game": game,
            "from_time": slot.start_time,
            "to_time": slot.end_time,
            "peak_price": peak_price
        }
    )

    return Response({
        "success": True,
        "message": "Peak hour price set",
        "peak_id": peak.id
    })
#------------------- delete peak hours --------------------------#
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def vendor_delete_peak_hour(request, peak_id):

    try:
        peak = PeakHour.objects.get(id=peak_id, turf__owner=request.user)
        peak.delete()
        return Response({"success": True})
    except PeakHour.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    
# ----------------------location--------------------------------------------
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Location
from .serializers import LocationSerializer


# GET all locations
@api_view(["GET"])
def location_list(request):
    locations = Location.objects.all()
    serializer = LocationSerializer(locations, many=True)
    return Response(serializer.data)


# DEBUG ENDPOINT - Test if the endpoint is reachable
@api_view(["GET", "POST"])
def test_select_location(request):
    return Response({
        "status": "ok",
        "method": request.method,
        "data": request.data
    })

# SELECT LOCATION - Fixed with auto-creation and better matching
@api_view(["POST"])
def select_location(request):
    city_name = request.data.get("city")

    print(f"DEBUG: Received city_name = {city_name}")  # Add debug print

    if not city_name:
        return Response({"error": "City required"}, status=400)

    # Normalize city name - capitalize first letter
    city_normalized = city_name.strip().title()

    try:
        # Try exact match first (case-insensitive)
        location = Location.objects.get(name__iexact=city_name)
        print(f"DEBUG: Found exact location = {location.name}")  # Add debug print

        return Response({
            "location_id": location.id,
            "location_name": location.name
        })

    except Location.DoesNotExist:
        print(f"DEBUG: Exact location not found, trying partial match for city = {city_name}")  # Add debug print

        # Try partial match - city name contains or is contained by
        try:
            location = Location.objects.filter(
                name__icontains=city_name
            ).first()

            if location:
                print(f"DEBUG: Found partial match location = {location.name}")  # Add debug print
                return Response({
                    "location_id": location.id,
                    "location_name": location.name
                })
        except Exception as e:
            print(f"DEBUG: Partial match error: {e}")  # Add debug print

        # Last resort: Auto-create the location if it doesn't exist
        # This ensures the app works even without seeded location data
        try:
            location = Location.objects.create(
                name=city_normalized
            )
            print(f"DEBUG: Auto-created location = {location.name}")  # Add debug print

            return Response({
                "location_id": location.id,
                "location_name": location.name
            })

        except Exception as e:
            print(f"DEBUG: Auto-create error: {e}")  # Add debug print
            return Response({"error": "Location not available"}, status=404)

# --------------------booking summary------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_summary(request, booking_id):
    try:
        booking = Booking.objects.select_related(
            "payment", "game", "turf"
        ).get(
            id=booking_id,
            user=request.user
        )

        return Response({
            "booking_id": booking.id,
            "date": booking.date,
            "turf_name": booking.turf.name,
            "game_name": booking.game.game_name,

            "slots": [
                {
                    "start_time": s.start_time.strftime("%I:%M %p"),
                    "end_time": s.end_time.strftime("%I:%M %p"),
                    "price": s.price
                }
                for s in booking.slots.all()
            ],

            "original_amount": booking.original_amount,
            "advance_amount": booking.advance_amount,
            "service_charge": booking.service_charge,
            "total_price": booking.total_payable,  # ✅ FIXED

            "payment": {
                "status": booking.payment.status if hasattr(booking, "payment") else "N/A",
                "amount": booking.payment.amount if hasattr(booking, "payment") else 0,
                "razorpay_payment_id": booking.payment.razorpay_payment_id if hasattr(booking, "payment") else None,
            }
        })

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=404)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_latest_booking(request):
    try:
        booking = (
            Booking.objects
            .filter(user=request.user, status="CONFIRMED")
            .select_related("payment", "game", "turf")
            .order_by("-id")
            .first()
        )

        if not booking:
            return Response({"error": "No booking found"}, status=404)

        return Response({
            "booking_id": booking.id,
            "date": booking.date,
            "turf_name": booking.turf.name,
            "game_name": booking.game.game_name,

            "slots": [
                {
                    "start_time": s.start_time.strftime("%I:%M %p"),
                    "end_time": s.end_time.strftime("%I:%M %p"),
                    "price": s.price
                }
                for s in booking.slots.all()
            ],

            "original_amount": booking.original_amount,
            "advance_amount": booking.advance_amount,
            "service_charge": booking.service_charge,
            "total_price": booking.total_payable,  # ✅ FIXED

            "payment": {
                "status": booking.payment.status if hasattr(booking, "payment") else "N/A",
                "razorpay_payment_id": booking.payment.razorpay_payment_id if hasattr(booking, "payment") else None,
            }
        })

    except Exception as e:
        print("Summary error:", str(e))
        return Response({"error": "Something went wrong"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_all_bookings(request):
    try:
        print("Logged in user:", request.user)
        print("User ID:", request.user.id)

        bookings = (
            Booking.objects
            .filter(user=request.user)
            .select_related("game", "turf")
            .prefetch_related("slots")
            .order_by("-id")
        )

        if not bookings.exists():
            return Response([], status=200)   # 🔥 return empty list (not 404)

        booking_data = []

        for booking in bookings:

            # 🔥 Get related payment properly
            payment = Payment.objects.filter(booking=booking).first()

            booking_data.append({
                "booking_id": booking.id,
                "date": booking.date,
                "turf_name": booking.turf.name,
                "game_name": booking.game.game_name,

                "slots": [
                    f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
                    for slot in booking.slots.all()
                ],

                "total_price": booking.total_payable,

                "payment_status": payment.status if payment else "PENDING",
            })

        return Response(booking_data)

    except Exception as e:
        print("Booking list error:", str(e))
        return Response({"error": "Something went wrong"}, status=500)


# ----------------------user profile update------------------------------------------------
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """Update user profile - name, mobile"""
    try:
        user = request.user
        
        # Get data from request
        name = request.data.get("name")
        mobile = request.data.get("mobile")
        
        # Update fields if provided
        if name:
            user.name = name
        if mobile:
            user.mobile = mobile
            
        user.save()
        
        return Response({
            "success": True,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "mobile": user.mobile
            }
        })
        
    except Exception as e:
        print("Profile update error:", str(e))
        return Response({"error": "Failed to update profile"}, status=500)
