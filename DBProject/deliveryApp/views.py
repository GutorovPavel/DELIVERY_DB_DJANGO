import datetime

import psycopg2
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.db import connection
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
            cursor.execute(f"INSERT INTO orders(create_time, deliver_time, client_id, status_id, total_price) " +
                           f"VALUES('{datetime.date.today()} {datetime.datetime.now().strftime('%H:%M:%S')}', null, 1, 1, {price});")

        context = {
            'dishes': order_items,
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
            cursor.execute(f"INSERT INTO users(email, phone, first_name, last_name) VALUES ({', '.join(data[:4])});" +
                           f"INSERT INTO clients(address, user_id) VALUES ({data[4]}, {i + 1})")

        return HttpResponseRedirect('/')

    context = {
        'form': form,
    }

    return render(request, PAGE_PATH + 'signin.html', context=context)
