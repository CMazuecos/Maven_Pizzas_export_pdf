import pandas as pd
from fpdf import FPDF
import datetime
import re
import numpy as np
import matplotlib.pyplot as plt

def informe_calidad_datos (fichero, name):
    #Print name of the file, nans, nulls and data types
    print('Nombre del fichero:', name)
    print (fichero.isnull().sum()) 
    print (fichero.dtypes)
    print (fichero.isna().sum())
    datatype_dictionary = {}
    #escribir en un datatype_dictionary, como key el nombre de la columna y como value el tipo de dato
    for i in range(len(fichero.columns)):
        datatype_dictionary[fichero.columns[i]] = fichero.dtypes[i]
    #Number of nulls values
    print (fichero.isnull().sum())
    return datatype_dictionary
def limpiar_fichero_order_details(fichero):
    print(fichero)
    print('Limpiando fichero order_details')
    #we change nan values to 1
    fichero['quantity'].fillna(1, inplace=True)
    fichero['quantity'] = fichero['quantity'].apply(lambda quantity: change_quantity(quantity))
    #we change the nan values of the column pizza_id to the value above
    fichero['pizza_id'].fillna(method='ffill', inplace=True)
    fichero['pizza_id'] = fichero['pizza_id'].apply(lambda pizza_id: change_pizza_id(pizza_id))
    print('Fichero order_details limpio')
    return fichero  

def change_quantity(quantity):
    #change in the column quantity the values that are not numbers to their numbers and if they are less than 1 we change them to 1
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
        return quantity
    except:
        quantity = re.sub(r'one', '1', quantity, flags=re.IGNORECASE)
        quantity = re.sub(r'two', '2', quantity, flags=re.IGNORECASE)
        return quantity

def change_pizza_id(pizza_id):
    #convert some characters to others 
    pizza_id = re.sub('@', 'a', pizza_id)
    pizza_id = re.sub('0', 'o', pizza_id)
    pizza_id = re.sub('1', 'i', pizza_id)
    pizza_id = re.sub('3', 'e', pizza_id)
    pizza_id = re.sub('-', '_', pizza_id)
    pizza_id = re.sub(' ', '_', pizza_id)
    return pizza_id


def limpieza_datos_orders(fichero):
    fichero = fichero.sort_values(by=['order_id'])
    #fichero fillna with values above
    print(fichero)
    print('Limpiando fichero orders')
    fichero.fillna(method='ffill', inplace=True) # we fill the nan values with the value above
    #change column date to datetime
    fichero['date'] = fichero['date'].apply(lambda x: change_date(x))    
    print('Fichero orders limpio') 
    return fichero

def change_date(date):
    try:
        #change the date to datetime
        date = pd.to_datetime(date)
        return date
    except:
        #change the date (written in seconds) to the correct format
        date = datetime.datetime.fromtimestamp(int(float(date)))
        return date

def create_dictionary(pizza_types):
    #create a dictionary with the pizza type id as key and the ingredients as value 
    dictionary_pizza_type = {}
    for i in range(len(pizza_types)):
        dictionary_pizza_type [pizza_types ['pizza_type_id'][i]] = pizza_types ['ingredients'] [i]
    return dictionary_pizza_type


def cargar_datos (order_details, pizzas, pizza_types, orders):
    dictionary_pizza_type = create_dictionary(pizza_types) 
    semanas, dias_semana = organizar_por_semanas(orders) #get the weeks and the days of the week
    pedidos, tamanos_cantidad, dinero = organizar_por_pedidos(semanas, order_details, dictionary_pizza_type, pizzas) #get the orders, the sizes and the money
    ingredients_dictionary = {}
    for i in range(len(pedidos)):

        ingredients_week = transform_pizza_into_ingredients(pedidos[i], dias_semana[i], pizza_types, {})
        ingredients_dictionary [i+1] = ingredients_week #add the total ingredients of each week to the dictionary
        print('Cargado los ingredientes de la semana', i+1) 
    return ingredients_dictionary, pedidos, tamanos_cantidad, dinero

def organizar_por_semanas(orders):
    diccionario_weekdays = {}
    diccionario_pedidos = {}
    for i in range (53):
        diccionario_weekdays [i] = [0, 0, 0, 0, 0, 0, 0]
        diccionario_pedidos [i] = [] 

    for order in orders['order_id']:
        #get the week of the order
        try:
            fecha = orders['date'][order]
            numero_semana = fecha.isocalendar().week
            numero_dia = fecha.isocalendar().weekday
            diccionario_weekdays [numero_semana-1][numero_dia-1] += 1
            diccionario_pedidos [numero_semana-1].append(orders['order_id'][order])
        except:
            pass
    for i in range(len(diccionario_weekdays)):
        #get the days of the week
        dias_semana = 0
        for j in range(len(diccionario_weekdays[i])):
            if diccionario_weekdays[i][j] != 0:
                dias_semana += 1
        diccionario_weekdays[i] = dias_semana
    return diccionario_pedidos, diccionario_weekdays

def organizar_por_pedidos(semanas, order_details, dictionary_pizza_type, pizzas):
    tamanos = {'S': 1, 'M': 2, 'L': 3, 'XL': 4, 'XXL': 5}
    cantidad_tamanos = {'S': 0, 'M': 0, 'L': 0, 'XL': 0, 'XXL': 0}
    pedidos_semana = []
    dinero = []
    for i in range(len(semanas)):
        dinero_semana = 0
        pedidos_semana.append({})
        for key, value in dictionary_pizza_type.items():
            pedidos_semana[i][key] = 0
        

        for j in range(len(semanas[i])):
            order_id_buscado = semanas[i][j]
            lista_pizzas = order_details.loc[order_details['order_id'] == order_id_buscado]
            for pizza in lista_pizzas['pizza_id']:
                pizza_searched = pizzas.loc[pizzas['pizza_id'] == pizza]
                dinero_semana += pizza_searched['price'].values[0] #get the money of the pizza
                quantity = lista_pizzas.loc[lista_pizzas['pizza_id'] == pizza]['quantity'].values[0]
                pizza_type = pizza_searched['pizza_type_id'].values[0]
                pizza_size = pizza_searched['size'].values[0]
                cantidad_tamanos[pizza_size] += 1 #add the size of the pizza to the dictionary
                pedidos_semana[i][pizza_type] += int(quantity) * int(tamanos[pizza_size])
        #con el dinero sumado, aproximarlo a 2 decimales y añadirlo a la lista de dinero
        dinero_semana = round(dinero_semana, 2)
        dinero.append(dinero_semana)
        print('Cargado el pedido de la semana', i+1)
    return pedidos_semana, cantidad_tamanos, dinero

def transform_pizza_into_ingredients(pizzas_semana, dias_semana, pizza_types, ingredients_dictionary):    
    #get the ingredients of the pizzas of the week
    for i in range(len(pizza_types)):
        ingredients = pizza_types['ingredients'][i]
        ingredients = ingredients.split(', ')
        for ingredient in ingredients:
            ingredients_dictionary[ingredient] = 0
    #add the ingredients of the pizzas of the week to the dictionary
    for key, value in pizzas_semana.items():
        ingredients = pizza_types.loc[pizza_types['pizza_type_id'] == key]['ingredients'].values[0]
        ingredients = ingredients.split(', ')
        for ingredient in ingredients:
            ingredients_dictionary[ingredient] += value
    for key, value in ingredients_dictionary.items():
        ingredients_dictionary[key] = int(np.ceil(value/dias_semana*7))
    return ingredients_dictionary

def extract_data():
    datatype_dictionary = {'order_details': {}, 'order_details': {}, 'pizza_types': {}, 'orders': {}}
    order_details = pd.read_csv('order_details.csv',sep=';')
    datatype_od = informe_calidad_datos(order_details, 'order_details.csv')
    datatype_dictionary['order_details'] = datatype_od
    order_details = limpiar_fichero_order_details(order_details)
    pizzas = pd.read_csv('pizzas.csv',sep = ',')
    datatype_p = informe_calidad_datos(pizzas, 'pizzas.csv')
    datatype_dictionary['pizzas'] = datatype_p
    pizza_types = pd.read_csv('pizza_types.csv', sep = ',', encoding='latin-1')
    datatype_pt = informe_calidad_datos(pizza_types, 'pizza_types.csv')
    datatype_dictionary['pizza_types'] = datatype_pt
    orders = pd.read_csv('orders.csv', sep = ';')
    datatype_o = informe_calidad_datos(orders, 'orders.csv')
    datatype_dictionary['orders'] = datatype_o
    orders = limpieza_datos_orders(orders)
    return order_details, pizzas, pizza_types, orders, datatype_dictionary

def calcular_pedidos_totales(pedidos):
    pedidos_totales = {}
    for semana in pedidos:
        for key, value in semana.items():
            if key in pedidos_totales:
                pedidos_totales[key] += value
            else:
                pedidos_totales[key] = value
    return pedidos_totales

def load_data(ingredients, pedidos, tamanos_cantidad, dinero):
    pedidos_totales = calcular_pedidos_totales(pedidos)
    pdf = FPDF()
    #First page
    pdf.add_page()
    pdf.set_font('Times', 'B', 16)
    pdf.set_text_color(255, 0, 100)
    pdf.cell(200, 10, txt = 'Reporte Ejecutivo Maden Pizzas', ln = 1, align = 'C')
    pdf.image('logo.jpg', x = 20, y = 40, w = 170)
    pdf.set_font('Times', '', 10)
    pdf.cell(200, 10, txt = 'Hecho por Carlos Mazuecos', ln = 1, align = 'C')
    pdf.set_y(250)
    pdf.set_font('Times', '', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, txt = 'Fecha: 17-01-2017', align = 'R')
    #Second page
    pdf.add_page()
    pdf.set_font('Times', 'B', 12)
    pdf.cell(200, 10, txt = 'Introducción', ln = 1, align = 'L')

    pdf.set_font('Times', '', 8)
    #Introduction
    pdf.multi_cell(0, 5, txt = 'En esta reporte ejecutivo se muestra un resumen de algunos datos que se han obtenido de la base de datos de Maden Pizzas. Se analizarán un pequeño análisis de los pedidos, sobre las pizzas, los ingredientes y otros elementos de interés para la empresa.', align = 'J')
    #hacer una tabla con cada tipo de pizza y su cantidad de pedidos
    pdf.set_font('Times', 'B', 12)
    pdf.cell(200, 10, txt = 'Análisis de pedidos', ln = 1, align = 'L')
    pdf.set_font('Times', 'U', 10)
    pdf.cell(200, 10, txt = 'Pedidos totales por tipo de pizza', ln = 1, align = 'L')
    #calculamos cuantas veces se hace cada pedido
    pedidos_sorted, pedido_value = [], []
    for key, value in pedidos_totales.items():
        pedidos_sorted.append(key)
        pedido_value.append(value)
    pedido_value.sort()
    pedidos_sorted.sort(key = lambda x: pedidos_totales[x])
    pedidos_sorted.reverse()
    pedido_value.reverse()
    #Creamos la tabla
    pdf.set_fill_color(200, 255, 200)
    pdf.set_line_width(0.3)
    pdf.set_font('Times', 'B', 10)
    pdf.cell(50, 5, txt = 'Tipo de pizza', border = 1, align = 'C', fill = True)
    pdf.cell(50, 5, txt = 'Cantidad de pedidos', border = 1, align = 'C', fill = True)
    pdf.ln()
    pdf.set_font('Times', '', 6)
    for i in range(len(pedidos_sorted)):
        pdf.cell(50, 5, txt = pedidos_sorted[i], border = 1, align = 'C', fill = True)
        pdf.cell(50, 5, txt = str(pedido_value[i]), border = 1, align = 'C', fill = True)
        pdf.ln()
    #Creamos las gráficas
    pdf.add_page()
    #Creamos la gráfica de barras de los top 5 más pedidos
    pedidos_totales = {}
    for i in range(5):
        pedidos_totales[pedidos_sorted[i]] = pedido_value[i]
    plt.figure(figsize=(10, 5))
    plt.bar(range(len(pedidos_totales)), list(pedidos_totales.values()), align='center')
    plt.xticks(range(len(pedidos_totales)), list(pedidos_totales.keys()), fontsize = 10)
    plt.title('Most ordered pizzas')
    plt.savefig('most_ordered_pizzas.png')
    plt.close()
    pdf.image('most_ordered_pizzas.png', x = 20, y = 40, w = 170)
    pdf.set_y(250)

    #Creamos la gráfica de barras de los top 5 menos pedidos
    pedidos_sorted.reverse()
    pedido_value.reverse()
    pedidos_totales = {}
    for i in range(5):
        pedidos_totales[pedidos_sorted[i]] = pedido_value[i]
    plt.figure(figsize=(10, 5))
    plt.bar(range(len(pedidos_totales)), list(pedidos_totales.values()), align='center')
    plt.xticks(range(len(pedidos_totales)), list(pedidos_totales.keys()), fontsize = 10)
    plt.title('Less ordered pizzas')
    plt.savefig('less_ordered_pizzas.png')
    plt.close()
    pdf.image('less_ordered_pizzas.png', x = 20, y = 120, w = 170)
    #escribir texto analizando los resultados justo debajo de la gráfica
    pdf.set_font('Times', '', 8)
    pdf.set_y(250)
    pdf.multi_cell(0, 5, txt = 'En la tabla se pueden ver ordenadas las pizzas por la cantidad de veces pedidas, de mayor a menor. En la primera gráfica de barras se muestran las 5 pizzas más pedidas, siendo la más solicitada la Thai Chicken pizza. En la siguiente gráfica se muestran las 5 pizzas menos pedidas. Se puede observar que con mucha diferencia, la pizza menos pedida es The Brie Carre Pizza.', align = 'J')
    #create a pie chart with tamanos_cantidad under the text
    pdf.add_page()
    pdf.set_font('Times', 'U', 10)
    pdf.cell(200, 10, txt = 'Tamaño de las pizzas', ln = 1, align = 'L')
    pdf.set_font('Times', '', 8)
    pdf.multi_cell(0, 5, txt = 'En la siguiente gráfica se muestra la cantidad de pizzas pedidas por tamaño. Se observa que la más pedida es la L y las pizzas xxl y xl se piden considerablemente menos que el resto de pizzas.', align = 'J')
    #Creamos la gráfica de tamaños
    plt.figure(figsize=(10, 5))
    tamanos, cantidad = [], []
    for key, value in tamanos_cantidad.items():
        tamanos.append(key)
        cantidad.append(value)
    #Por estetica cambiamos de sitio xxl y s
    cantidad[0], cantidad[-1], tamanos[0], tamanos[-1] = cantidad[-1], cantidad[0], tamanos[-1], tamanos[0]
    #make the labels of the pie chart smaller
    plt.pie(cantidad, labels = tamanos, autopct = '%1.1f%%')
    plt.title('Pizza sizes')
    plt.savefig('pizza_sizes.png')
    plt.close()
    pdf.image('pizza_sizes.png', x = 20, y = 40, w = 170)
    pdf.ln()


    #create a pie chart with toppings_cantidad under the text
    pdf.add_page()
    pdf.set_font('Times', 'B', 12)
    pdf.cell(200, 10, txt = 'Análisis de ingredientes', ln = 1, align = 'L')
    pdf.set_font('Times', 'U', 10)
    pdf.cell(200, 10, txt = 'Ingredientes más utilizados', ln = 1, align = 'L')
    pdf.set_font('Times', '', 8)
    pdf.multi_cell(0, 5, txt = 'En la siguiente gráfica se muestra la cantidad que se necesitó en total cada ingrediente para el año entero.', align = 'J')
    #Creamos la gráfica de ingredientes
    plt.figure(figsize=(10, 5))
    ingredientes_totales = {}
    for i in range(len(ingredients)):
        for key, value in ingredients[i+1].items():
            if key in ingredientes_totales:
                ingredientes_totales[key] += value
            else:
                ingredientes_totales[key] = value
    ingredientes_sorted, cantidad_sorted = [], []
    for key, value in ingredientes_totales.items():
        ingredientes_sorted.append(key)
        cantidad_sorted.append(value)
    cantidad_sorted.sort()
    ingredientes_sorted.sort(key = lambda x: ingredientes_totales[x])
    ingredientes_sorted.reverse()
    cantidad_sorted.reverse()
    #Creamos un grafico de barras con colores, bbox inches es para que no se corte la leyenda 
    plt.bar(range(len(ingredientes_sorted)), cantidad_sorted, align='center', color = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'grey', 'black'])
    plt.xticks(range(len(ingredientes_sorted)), ingredientes_sorted, rotation = 90, fontsize = 6)
    
    plt.title('Pizza ingredients')
    plt.savefig('pizza_ingredients.png', bbox_inches = 'tight')
    plt.close()
    pdf.image('pizza_ingredients.png', x = 20, y = 40, w = 170)
    #escribir debajo de la imagen
    pdf.set_y(170)
    pdf.multi_cell(0, 5, txt = 'Se puede observar que los ingredientes que con más se utilizaron con diferencia fueron los tomates y el ajo y en un nivel inferior, la cebolla y pepperoni. A partir de ahí, los ingredientes necesitados no superan los 2000. El elemento menos pedido es el queso brie carre, que coincide con que la pizza brie carre es la menos demandada en el restaurante.', align = 'J')
    #top 10 most ordered ingredients under pizza_ingrediets.png
    pdf.add_page()
    pdf.set_font('Times', 'U', 10)
    pdf.cell(200, 10, txt = 'Ingredientes más pedidos', ln = 1, align = 'L')
    plt.figure(figsize=(10, 5))
    ingredientes_sorted_top_10 = ingredientes_sorted[:10]
    cantidad_sorted_top_10 = cantidad_sorted[:10]
    plt.bar(range(len(ingredientes_sorted_top_10)), cantidad_sorted_top_10, align='center')
    plt.xticks(range(len(ingredientes_sorted_top_10)), ingredientes_sorted_top_10, rotation = 45, fontsize = 10)
    plt.title('Top 10 pizza ingredients')
    plt.savefig('pizza_ingredients_top_10.png', bbox_inches = 'tight')
    plt.close()
    pdf.image('pizza_ingredients_top_10.png', x = 20, y = 40, w = 170)
    plt.figure(figsize=(10, 5))
    ingredientes_sorted_bottom_10 = ingredientes_sorted[-10:]
    cantidad_sorted_bottom_10 = cantidad_sorted[-10:]
    plt.bar(range(len(ingredientes_sorted_bottom_10)), cantidad_sorted_bottom_10, align='center')
    plt.xticks(range(len(ingredientes_sorted_bottom_10)), ingredientes_sorted_bottom_10, rotation = 45, fontsize = 10)
    plt.title('Bottom 10 pizza ingredients')
    plt.savefig('pizza_ingredients_bottom_10.png', bbox_inches = 'tight')
    plt.close()
    pdf.image('pizza_ingredients_bottom_10.png', x = 20, y = 160, w = 170)
    pdf.add_page()
    #evolucion de dinero por semana
    pdf.set_font('Times', 'B', 12)
    pdf.cell(200, 10, txt = 'Análisis de dinero', ln = 1, align = 'L')
    pdf.set_font('Times', 'U', 10)
    pdf.cell(200, 10, txt = 'Evolución de dinero por semana', ln = 1, align = 'L')
    #mostrar la evolucion de dinero por semana y que empiece en 0
    
    pdf.set_font('Times', '', 8)
    pdf.multi_cell(0, 5, txt = 'En la siguiente gráfica se muestra la evolución del dinero que se ha ganado por semana a lo largo del año.', align = 'J')
    plt.figure(figsize=(10, 5))
    #hacer que la grafica empiece en 0
    plt.plot(range(len(dinero)), dinero)
    plt.xticks(range(len(dinero)), [i for i in range(1, len(dinero)+1)], rotation = 90, fontsize = 6)
    plt.yticks(range(0, int(max(dinero)+1), 1000))
    plt.title('Money evolution per week')
    plt.savefig('money_evolution.png', bbox_inches = 'tight')
    plt.close()
    pdf.image('money_evolution.png', x = 20, y = 40, w = 170)
    pdf.set_y(170)
    pdf.multi_cell(0, 5, txt = 'Se puede observar que el dinero que se ha ganado por semana ha ido variando, entre 13k y 18k euros, salvo la última semana que desciende a 8k (no es una semana de 7 días).', align = 'J')
    mean_money = sum(dinero)/len(dinero)
    pdf.set_y(185)
    pdf.multi_cell(0, 5, txt = 'Dinero medio ganado por semana: {} euros.'.format(round(mean_money, 2)), align = 'J')
    pdf.set_y(190)
    pdf.multi_cell(0, 5, txt = 'La semana que más dinero se ha ganado ha sido la {} y la semana que menos dinero se ha ganado ha sido la {}.'.format(dinero.index(max(dinero))+1, dinero.index(min(dinero))+1), align = 'J')
    pdf.output("Executive_Report.pdf")  






    





        
    
if __name__ == '__main__':
    order_details, pizzas, pizza_types, orders, datatype_dictionary = extract_data()
    ingredients, pedidos, tamanos_cantidad, dinero = cargar_datos(order_details, pizzas, pizza_types, orders)
    load_data(ingredients, pedidos, tamanos_cantidad, dinero)