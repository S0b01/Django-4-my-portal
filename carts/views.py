# Импорты стандартных модулей Django
from django.http import JsonResponse          # Для возврата JSON-ответов (AJAX)
from django.template.loader import render_to_string  # Для рендеринга HTML-фрагментов
from django.urls import reverse               # (не используется в текущих классах, но может пригодиться)
from django.views import View                 # Базовый класс для представлений

# Импорты из приложений проекта
from carts.mixins import CartMixin            # Миксин с общей логикой для работы с корзиной
from carts.models import Cart                 # Модель корзины
from carts.utils import get_user_carts        # Функция для получения корзины пользователя/сессии

from goods.models import Products             # Модель товара


# ============================================================
# 1. Представление для ДОБАВЛЕНИЯ товара в корзину
# ============================================================
class CartAddView(CartMixin, View):
    """
    Обрабатывает POST-запрос на добавление товара в корзину.
    Используется через AJAX (возвращает JSON).
    Наследует CartMixin (даёт методы get_cart и render_cart) и View.
    """

    def post(self, request):
        """
        Получает product_id из POST-данных, находит товар,
        добавляет его в корзину (или увеличивает количество),
        и возвращает JSON с сообщением и обновлённым HTML-кодом корзины.
        """
        # 1. Получаем ID товара из запроса
        product_id = request.POST.get("product_id")
        # 2. Находим товар в БД (если не найден – будет исключение 404)
        product = Products.objects.get(id=product_id)

        # 3. Получаем или создаём запись корзины для данного товара
        #    Метод get_cart предоставлен CartMixin. Он учитывает:
        #    - авторизован ли пользователь (использует user или session_key)
        #    - если запись уже есть – возвращает её, иначе None
        cart = self.get_cart(request, product=product)

        if cart:
            # Если запись существует – увеличиваем количество на 1
            cart.quantity += 1
            cart.save()
        else:
            # Иначе создаём новую запись
            # Определяем, кто пользователь: если авторизован – берём request.user,
            # иначе – None (для анонимов)
            user = request.user if request.user.is_authenticated else None
            # Для анонимов берём session_key из сессии (если нет – создаётся автоматически)
            session_key = request.session.session_key if not request.user.is_authenticated else None
            Cart.objects.create(
                user=user,
                session_key=session_key,
                product=product,
                quantity=1
            )

        # 4. Формируем ответ для клиента
        response_data = {
            "message": "Товар добавлен в корзину",          # Сообщение для пользователя
            'cart_items_html': self.render_cart(request)   # Обновлённый HTML-фрагмент корзины
        }

        # 5. Возвращаем JSON-ответ (фронтенд обработает его и обновит интерфейс)
        return JsonResponse(response_data)


# ============================================================
# 2. Представление для ИЗМЕНЕНИЯ количества товара в корзине
# ============================================================
class CartChangeView(CartMixin, View):
    """
    Обрабатывает POST-запрос на изменение количества товара в корзине.
    Возвращает JSON с новым количеством и обновлённым HTML-фрагментом.
    """

    def post(self, request):
        # 1. Получаем ID записи корзины и новое количество
        cart_id = request.POST.get("cart_id")
        new_quantity = request.POST.get("quantity")  # приходит как строка

        # 2. Находим запись корзины через метод get_cart (из CartMixin)
        #    Передаём cart_id, чтобы получить конкретную запись
        cart = self.get_cart(request, cart_id=cart_id)

        # 3. Обновляем количество и сохраняем
        cart.quantity = new_quantity
        cart.save()

        # 4. Формируем ответ
        response_data = {
            "message": "Количество изменено",
            "quantity": cart.quantity,                     # новое количество (число)
            'cart_items_html': self.render_cart(request)   # обновлённый HTML корзины
        }

        return JsonResponse(response_data)


# ============================================================
# 3. Представление для УДАЛЕНИЯ товара из корзины
# ============================================================
class CartRemoveView(CartMixin, View):
    """
    Обрабатывает POST-запрос на удаление товара из корзины.
    Возвращает JSON с сообщением и обновлённым HTML-фрагментом.
    """

    def post(self, request):
        # 1. Получаем ID записи корзины
        cart_id = request.POST.get("cart_id")

        # 2. Находим запись через get_cart
        cart = self.get_cart(request, cart_id=cart_id)

        # 3. Запоминаем количество (для ответа) и удаляем запись
        quantity_deleted = cart.quantity
        cart.delete()

        # 4. Формируем ответ
        response_data = {
            "message": "Товар удален из корзины",
            "quantity_deleted": quantity_deleted,          # сколько было удалено
            'cart_items_html': self.render_cart(request)   # обновлённый HTML корзины
        }

        return JsonResponse(response_data)