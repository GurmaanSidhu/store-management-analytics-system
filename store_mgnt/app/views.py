from rest_framework.decorators      import api_view, permission_classes
from rest_framework.response        import Response
from rest_framework.permissions     import IsAuthenticated
from rest_framework                 import status
from django.db                      import transaction
from .models                        import InventoryLog, InventoryLog, Sale, SaleItem, Product, User, Shift
from django.shortcuts               import render, redirect
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models               import Sum, Count
from django.utils                   import timezone
from .serializers                   import ProductSerializer



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_list(request):
    products = Product.objects.all()
    data = []

    for product in products:
        data.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity
        })

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sale(request):

    if request.user.role != "EMPLOYEE":
        return Response({"error": "Only employees can create sales."}, status=403)

    items = request.data.get("items")

    if not items:
        return Response({"error": "No items provided"}, status=400)

    total_amount = 0

    with transaction.atomic():  # ensures all or nothing

        sale = Sale.objects.create(
            employee=request.user,
            total_amount=0
        )

        for item in items:
            product = Product.objects.get(id=item["product_id"])
            quantity = item["quantity"]

            if product.quantity < quantity:
                return Response({"error": f"Not enough stock for {product.name}"}, status=400)

            product.quantity -= quantity
            product.save()

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                price_at_sale=product.price
            )

            total_amount += product.price * quantity

        sale.total_amount = total_amount
        sale.save()

    return Response({"message": "Sale recorded successfully"})



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


@login_required
def dashboard_view(request):
    user = request.user

    context = {
        "username": user.username,
        "role": user.role
    }

    return render(request, "dashboard.html", context)


@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, "products.html", {"products": products})

@login_required
def add_product(request):

    if request.user.role not in ["CEO", "MANAGER"]:
        return redirect("dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity")

        Product.objects.create(
            name=name,
            price=price,
            quantity=quantity
        )

        return redirect("products")

    return render(request, "add_product.html")



@login_required
def create_sale(request):

    if request.user.role != "EMPLOYEE":
        return redirect("dashboard")

    products = Product.objects.all()

    if request.method == "POST":
        product_id = request.POST.get("product")
        quantity = int(request.POST.get("quantity"))

        product = Product.objects.get(id=product_id)

        if product.quantity < quantity:
            return render(request, "create_sale.html", {
                "products": products,
                "error": "Not enough stock!"
            })

        with transaction.atomic():

            sale = Sale.objects.create(
                employee=request.user,
                total_amount=0
            )

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                price_at_sale=product.price
            )

            product.quantity -= quantity
            product.save()

            sale.total_amount = product.price * quantity
            sale.save()

        return redirect("sale_history")

    return render(request, "create_sale.html", {"products": products})

@login_required
def sale_history(request):

    if request.user.role == "EMPLOYEE":
        sales = Sale.objects.filter(employee=request.user)
    else:
        sales = Sale.objects.all()

    return render(request, "sale_history.html", {"sales": sales})

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def ceo_dashboard(request):
    if request.user.role != "CEO":
        return redirect("dashboard")
    total_revenue = Sale.objects.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    total_sales = Sale.objects.count()
    low_stock_products = Product.objects.filter(quantity__lt=5) # quantity_lt=5 -> where quantity < 5 (__lt mean less than)

    employee_sales = (
        User.objects
        .filter(role="EMPLOYEE")
        .annotate(
            total_sales=Sum("sale__total_amount")
        )
    )

    manager_activity = (
        User.objects
        .filter(role="MANAGER")
        .annotate(
            total_adjustments=Count("inventorylog"),
            total_stock_changed=Sum("inventorylog__adjustment")
        )
    )

    return render(request, "ceo_dashboard.html", {
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "low_stock_products": low_stock_products,
        "employee_sales": employee_sales,
        "manager_activity": manager_activity,
    })

@login_required
def hr_employee_list(request):

    if request.user.role != "HR":
        return redirect("dashboard")

    employees = User.objects.exclude(role="CEO")

    return render(request, "hr_employees.html", {
        "employees": employees
    })

@login_required
def update_salary(request, user_id):

    if request.user.role != "HR":
        return redirect("dashboard")

    employee = User.objects.get(id=user_id)

    if employee.role == "CEO":
        return redirect("hr_employees")

    if request.method == "POST":
        new_salary = request.POST.get("salary")
        employee.salary = new_salary
        employee.save()
        return redirect("hr_employees")

    return render(request, "update_salary.html", {
        "employee": employee
    })

@login_required
def adjust_inventory(request, product_id):

    if request.user.role != "MANAGER":
        return redirect("dashboard")

    product = Product.objects.get(id=product_id)

    if request.method == "POST":
        adjustment = int(request.POST.get("adjustment"))

        if product.quantity + adjustment < 0:
            return render(request, "adjust_inventory.html", {
                "product": product,
                "error": "Stock cannot go negative!"
            })

        product.quantity += adjustment
        product.save()

        InventoryLog.objects.create(
            manager=request.user,
            product=product,
            adjustment=adjustment
)

        return redirect("products")

    return render(request, "adjust_inventory.html", {
        "product": product
    })


@login_required
def check_in(request):

    if request.user.role != "EMPLOYEE":
        return redirect("dashboard")

    today = timezone.now().date()

    shift, created = Shift.objects.get_or_create(
        employee=request.user,
        date=today
    )

    if shift.check_in is None:
        shift.check_in = timezone.now()
        shift.save()

    return redirect("dashboard")

@login_required
def check_out(request):

    if request.user.role != "EMPLOYEE":
        return redirect("dashboard")

    today = timezone.now().date()

    try:
        shift = Shift.objects.get(employee=request.user, date=today)
        shift.check_out = timezone.now()
        shift.save()
    except Shift.DoesNotExist:
        pass

    return redirect("dashboard")

@login_required
def view_shifts(request):

    if request.user.role not in ["HR", "CEO"]:
        return redirect("dashboard")

    shifts = Shift.objects.all().order_by("-date")

    return render(request, "view_shifts.html", {"shifts": shifts})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def product_list_api(request):

    if request.method == 'GET':
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    if request.method == 'POST':

        if request.user.role not in ["CEO", "MANAGER"]:
            return Response(
                {"error": "You are not allowed to create products."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

