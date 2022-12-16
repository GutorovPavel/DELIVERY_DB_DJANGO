import datetime

import psycopg2
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db import connection
from django.template.defaulttags import url
from django.views import View

from . import forms

from .models import *

# Create your views here.

PAGE_PATH = 'deliveryApp/'


def dictfetchall(cursor):
    # "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def index(request):
    with connection.cursor() as cursor:
        cursor.execute("select * from restaurants")
        rests = dictfetchall(cursor)

    context = {
        'rests': rests,
    }
    return render(request, PAGE_PATH + 'index.html', context=context)


def restaurant(request, r_id, t_id):
    with connection.cursor() as cursor:
        cursor.execute("select * from dish_types")
        t = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute("select * from dish_types")
        types = dictfetchall(cursor)

    with connection.cursor() as cursor:
        cursor.execute("select * from restaurants")
        r = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute("select * from dishes " +
                       "join dish_types using(dish_type_id) " +
                       "join restaurants_dishes using(dish_id) " +
                       "join restaurants using(restaurant_id) " +
                       f"where restaurant_id = {r[r_id - 1][0]} and dish_type_id = {t[t_id - 1][0]}")
        dishes = dictfetchall(cursor)

    context = {
        'dishes': dishes,
        'types': types,
    }
    return render(request, PAGE_PATH + 'dishes.html', context=context)


class Order(View):
    def get(self, request, r_id, t_id, **kwargs):

        with connection.cursor() as cursor:
            cursor.execute("select * from dish_types")
            t = cursor.fetchall()

        with connection.cursor() as cursor:
            cursor.execute("select * from dish_types")
            types = dictfetchall(cursor)

        with connection.cursor() as cursor:
            cursor.execute("select * from restaurants")
            r = cursor.fetchall()

        with connection.cursor() as cursor:
            cursor.execute("select * from dishes " +
                           "join dish_types using(dish_type_id) " +
                           "join restaurants_dishes using(dish_id) " +
                           "join restaurants using(restaurant_id) " +
                           f"where restaurant_id = {r[r_id - 1][0]} and dish_type_id = {t[t_id - 1][0]}")
            dishes = dictfetchall(cursor)

        context = {
            'dishes': dishes,
            'types': types,
        }
        return render(request, PAGE_PATH + 'dishes.html', context=context)

    def post(self, request, **kwargs):
        order_items = {
            'items': []
        }

        items = request.POST.getlist('items[]')

        for item in items:
            with connection.cursor() as cursor:
                cursor.execute(f"select * from dishes where dish_id = {int(item)}")
                order_item = cursor.fetchall()

            item_data = {
                'dish_id': order_item[0][0],
                'dish_name': order_item[0][1],
                'price': order_item[0][3]
            }

            order_items['items'].append(item_data)

        price = 0
        dish_ids = []

        for dish in order_items['items']:
            price += dish['price']
            dish_ids.append(dish['dish_id'])

        with connection.cursor() as cursor:
            cursor.execute("select max(order_id) from orders")
            o = cursor.fetchall()[0][0] + 1

        with connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO orders(create_time, deliver_time, client_id, status_id, total_price) " +
                           f"VALUES('{datetime.date.today()} {datetime.datetime.now().strftime('%H:%M:%S')}', null, 1, 1, {price});")
        with connection.cursor() as cursor:
            for i in range(len(dish_ids)):
                cursor.execute(f"INSERT INTO orders_dishes(order_id, dish_id) VALUES ({o}, {dish_ids[i]})")

        with connection.cursor() as cursor:
            cursor.execute(f"select dish_name from orders_dishes join dishes using(dish_id) where order_id = {o}")
            dishes = dictfetchall(cursor)

        context = {
            'dishes': dishes,
            'price': price,
        }
        return render(request, PAGE_PATH + 'submit_order.html', context=context)


def sign(request):
    form = forms.AddClientForm(request.POST or None)

    if form.is_valid():
        data = [
            form.cleaned_data.get('email'),
            form.cleaned_data.get('phone'),
            form.cleaned_data.get('first_name'),
            form.cleaned_data.get('last_name'),
            form.cleaned_data.get('address')
        ]

        for i in range(len(data)):
            data[i] = 'NULL' if data[i] == '' else f'\'{data[i]}\''

        with connection.cursor() as cursor:
            cursor.execute("select max(user_id) from users")
            i = cursor.fetchall()[0][0]

        with connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO users(email, phone, first_name, last_name) VALUES ({', '.join(data[:4])});"
                           +
                           f"INSERT INTO clients(address, user_id) VALUES ({data[4]}, {i+1})")

        return HttpResponseRedirect('/')

    context = {
        'form': form,
    }

    return render(request, PAGE_PATH + 'signin.html', context=context)


def profile(request):
    u_id = 1
    with connection.cursor() as cursor:
        cursor.execute(f"select * from clients join users using(user_id) where user_id = {u_id}")
        client_info = dictfetchall(cursor)

    context = {
        'client_info': client_info,
    }

    return render(request, PAGE_PATH + 'profile.html', context=context)


def edit_profile(request, u_id):
    form = forms.EditClientForm(request.POST or None)

    error = ''

    with connection.cursor() as cursor:
        cursor.execute(f"select * from clients join users using(user_id) where user_id = {u_id}")
        client_info = dictfetchall(cursor)

    if form.is_valid():
        email = form.cleaned_data.get('email')
        phone = form.cleaned_data.get('phone')
        first_name = form.cleaned_data.get('first_name')
        last_name = form.cleaned_data.get('last_name')
        address = form.cleaned_data.get('address')
        #
        # for i in range(len(data)):
        #     data[i] = 'NULL' if data[i] == '' else f'\'{data[i]}\''

        with connection.cursor() as cursor:
            cursor.execute(f"update users set email = '{email}', phone = '{phone}', " +
                           f"first_name = '{first_name}', last_name = '{last_name}' where user_id = {u_id};" +
                           f"update client set address = '{address}' where user_id = {u_id};")

        return HttpResponseRedirect('/')

    # else:
    #     return HttpResponseRedirect(f'/profile/edit/{u_id}')
    #     error = 'error'

    context = {
        'client_info': client_info,
        'form': form,
        'error': error
    }

    return render(request, PAGE_PATH + 'edit_profile.html', context=context)


def get_orders(request):
    with connection.cursor() as cursor:
        cursor.execute("select * from orders")
        orders = dictfetchall(cursor)

    with connection.cursor() as cursor:
        cursor.execute(f"select * from dishes join orders_dishes using(dish_id) where order_id = 1")
        dishes = dictfetchall(cursor)

    context = {
        'orders': orders,
        'dishes': dishes,
    }

    return render(request, PAGE_PATH + 'orders.html', context=context)


# def get_restaurants(request):
#     with connection.cursor() as cursor:
#         cursor.execute("select * from restaurants")
#         restaurants = dictfetchall(cursor)
#
#     context = {
#         'restaurants': restaurants,
#     }
#
#     return render(request, PAGE_PATH + 'restaurants.html', context=context)


class Restaurants(View):
    def get(self, request, *args, **kwargs):

        with connection.cursor() as cursor:
            cursor.execute("select * from restaurants")
            restaurants = dictfetchall(cursor)

        context = {
            'restaurants': restaurants,
        }

        return render(request, PAGE_PATH + 'restaurants.html', context=context)

    def post(self, request, **kwargs):
        restaurant_dict = {
            'items': []
        }

        items = request.POST.getlist('items[]')

        for item in items:
            with connection.cursor() as cursor:
                cursor.execute(f"select * from restaurants where restaurant_id = {int(item)}")
                restaurant = cursor.fetchall()

            item_data = {
                'restaurant_id': restaurant[0][0],
                'restaurant_name': restaurant[0][1],
            }

            restaurant_dict['items'].append(item_data)

        # price = 0
        restaurant_ids = []

        for rest in restaurant_dict['items']:
            restaurant_ids.append(rest['restaurant_id'])

        with connection.cursor() as cursor:
            for i in range(len(restaurant_ids)):
                cursor.execute(f"DELETE FROM restaurants where restaurant_id = {restaurant_ids[i]};")

        return HttpResponseRedirect('/')


class Employees(View):
    def get(self, request, *args, **kwargs):

        with connection.cursor() as cursor:
            cursor.execute("select * from employees join posts using(post_id) join users using(user_id)")
            employees = dictfetchall(cursor)

        context = {
            'employees': employees,
        }

        return render(request, PAGE_PATH + 'employees.html', context=context)

    def post(self, request, **kwargs):
        employees_dict = {
            'items': []
        }

        items = request.POST.getlist('items[]')

        for item in items:
            with connection.cursor() as cursor:
                cursor.execute(f"select * from employees join users using(user_id) where employee_id = {int(item)}")
                employee = cursor.fetchall()

            item_data = {
                'employee_id': employee[0][1],
            }

            employees_dict['items'].append(item_data)

        # price = 0
        employee_ids = []

        for emp in employees_dict['items']:
            employee_ids.append(emp['employee_id'])

        with connection.cursor() as cursor:
            for i in range(len(employee_ids)):
                cursor.execute(f"UPDATE employees SET salary = salary + 1000 where employee_id = {employee_ids[i]};")

        return HttpResponseRedirect('/employees')
