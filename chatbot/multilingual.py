"""
Multilingual helper module supporting English, Hindi (हिन्दी), and Spanish (Español).
Provides automatic language detection, translation dictionary, localized intent responses,
and localized quick replies.
"""

import re

SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'flag': '🇬🇧', 'voice_code': 'en-US', 'btn_add': '+ Add'},
    'hi': {'name': 'हिन्दी', 'flag': '🇮🇳', 'voice_code': 'hi-IN', 'btn_add': '+ जोड़ें'},
    'es': {'name': 'Español', 'flag': '🇪🇸', 'voice_code': 'es-ES', 'btn_add': '+ Añadir'}
}

# Common Spanish keywords for fast detection
SPANISH_KEYWORDS = {
    'hola', 'buenos', 'tardes', 'noches', 'dias', 'qué', 'que', 'dónde', 'donde', 'está', 'esta',
    'pedido', 'carrito', 'gracias', 'favor', 'comida', 'quiero', 'menú', 'menu', 'cuánto', 'cuanto',
    'hamburguesa', 'hamburguesas', 'pizza', 'pizzas', 'postre', 'postres', 'vegetariano', 'vegetariana',
    'pollo', 'carne', 'pagar', 'ayuda', 'recomiendas', 'recomienda', 'añadir', 'agregar', 'vaciar',
    'precio', 'costo', 'tiempo', 'entrega', 'ver', 'mostrar'
}

# Common Hindi / Hinglish keywords for detection
HINDI_KEYWORDS = {
    'namaste', 'namaskar', 'kaisa', 'kaise', 'kya', 'khana', 'dikhao', 'chahiye', 'kahan', 'mera',
    'meri', 'order', 'batao', 'jodo', 'daalo', 'shakahari', 'mansahari', 'meetha', 'kitna', 'kitne',
    'dam', 'keemat', 'shukriya', 'dhanyawad', 'alvida', 'madad', 'bhai', 'bolo', 'lao', 'pizzas'
}

def detect_language(text, fallback_lang='en'):
    """
    Intelligently detect whether the input text is in Hindi, Spanish, or English.
    """
    if not text:
        return fallback_lang

    # 1. Check for Devanagari script (Hindi: \u0900-\u097F)
    if re.search(r'[\u0900-\u097F]', text):
        return 'hi'

    text_lower = text.lower()
    words = set(re.findall(r'[a-záéíóúüñ]+', text_lower))

    # 2. Check for Spanish specific characters and keywords
    if any(c in text_lower for c in ['¿', '¡', 'á', 'é', 'í', 'ó', 'ú', 'ñ']):
        return 'es'

    spanish_overlap = words.intersection(SPANISH_KEYWORDS)
    hindi_overlap = words.intersection(HINDI_KEYWORDS)

    if len(spanish_overlap) >= 2 or (len(spanish_overlap) == 1 and len(words) <= 3 and any(w in spanish_overlap for w in ['hola', 'gracias', 'pedido', 'carrito', 'dónde'])):
        return 'es'

    if len(hindi_overlap) >= 2 or (len(hindi_overlap) == 1 and len(words) <= 3 and any(w in hindi_overlap for w in ['namaste', 'khana', 'dikhao', 'kahan', 'kya'])):
        return 'hi'

    return fallback_lang

TRANSLATIONS = {
    'GREETING': {
        'en': "Hello! 👋 I'm your **AI Food Assistant**. What are you craving today?",
        'hi': "नमस्ते! 🙏 मैं आपका **AI फ़ूड असिस्टेंट** हूँ। आज आप क्या खाना चाहेंगे?",
        'es': "¡Hola! 👋 Soy tu **Asistente de Comida IA**. ¿Qué se te apetece hoy?"
    },
    'GOODBYE': {
        'en': "Goodbye! 👋 Come back whenever you're hungry! Have a delicious day! 🍔",
        'hi': "अलविदा! 👋 जब भी भूख लगे वापस आएं! आपका दिन स्वादिष्ट रहे! 🍔",
        'es': "¡Hasta luego! 👋 ¡Vuelve cuando tengas hambre! ¡Que tengas un día delicioso! 🍔"
    },
    'THANKS': {
        'en': "Happy to help! 😊 Let me know if you need anything else! 🍽️",
        'hi': "आपकी मदद करके खुशी हुई! 😊 अगर आपको कुछ और चाहिए तो बताएं! 🍽️",
        'es': "¡Con mucho gusto! 😊 ¡Avísame si necesitas algo más! 🍽️"
    },
    'ADDED_TO_CART': {
        'en': "✅ Added **{quantity}x {item_name}** (₹{item_total}) to your cart! 🛒",
        'hi': "✅ **{quantity}x {item_name}** (₹{item_total}) आपकी कार्ट में जोड़ दिया गया है! 🛒",
        'es': "✅ ¡Se añadió **{quantity}x {item_name}** (₹{item_total}) a tu carrito! 🛒"
    },
    'ITEM_NOT_FOUND_SUGGEST': {
        'en': "Which food item would you like to add? Check our recommendations below: 👇",
        'hi': "आप कौन सा व्यंजन जोड़ना चाहेंगे? हमारे शीर्ष विकल्प नीचे देखें: 👇",
        'es': "¿Qué plato te gustaría añadir? Mira nuestras sugerencias a continuación: 👇"
    },
    'PRICE_RESPONSE': {
        'en': "💰 **{item_name}** is **₹{price}**.\n\n{description}\n\nWould you like to add one to your cart?",
        'hi': "💰 **{item_name}** की कीमत **₹{price}** है।\n\n{description}\n\nक्या आप इसे अपनी कार्ट में जोड़ना चाहते हैं?",
        'es': "💰 **{item_name}** cuesta **₹{price}**.\n\n{description}\n\n¿Deseas añadirlo a tu carrito?"
    },
    'BUDGET_FOUND': {
        'en': "Here are our best dishes under ₹{price_limit}: 💸",
        'hi': "₹{price_limit} से कम में हमारे सबसे बेहतरीन व्यंजन यहाँ हैं: 💸",
        'es': "Aquí tienes nuestros mejores platos por menos de ₹{price_limit}: 💸"
    },
    'BUDGET_NONE': {
        'en': "We couldn't find items under ₹{price_limit}, but you can explore our full budget-friendly menu! 🍽️",
        'hi': "हमें ₹{price_limit} से कम के व्यंजन नहीं मिले, लेकिन आप हमारे बजट-अनुकूल मेनू को देख सकते हैं! 🍽️",
        'es': "No encontramos platos por menos de ₹{price_limit}, ¡pero puedes explorar nuestro menú económico! 🍽️"
    },
    'ORDER_STATUS_LOGIN_REQUIRED': {
        'en': "🔒 Please **log in** to track your personalized order history and status!",
        'hi': "🔒 अपने व्यक्तिगत ऑर्डर की स्थिति देखने के लिए कृपया **लॉगिन** करें!",
        'es': "🔒 ¡Por favor **inicia sesión** para rastrear tu historial y estado de pedidos!"
    },
    'ORDER_STATUS_NONE': {
        'en': "You don't have any recent orders yet. Hungry? Ready to order something delicious? 🍕",
        'hi': "आपके पास अभी कोई हालिया ऑर्डर नहीं है। क्या आप कुछ स्वादिष्ट ऑर्डर करना चाहते हैं? 🍕",
        'es': "Aún no tienes pedidos recientes. ¿Tienes hambre? ¿Listo para pedir algo delicioso? 🍕"
    },
    'ORDER_STATUS_TEMPLATE': {
        'en': "📦 **Order #{order_id}**\n\n• **Status:** {status_desc}\n• **Items:** {items_str}\n• **Total:** ₹{total_price}\n• **Delivery to:** {address}\n• **Ordered on:** {date}",
        'hi': "📦 **ऑर्डर #{order_id}**\n\n• **स्थिति:** {status_desc}\n• **सामग्री:** {items_str}\n• **कुल:** ₹{total_price}\n• **डिलीवरी पता:** {address}\n• **तारीख:** {date}",
        'es': "📦 **Pedido #{order_id}**\n\n• **Estado:** {status_desc}\n• **Platos:** {items_str}\n• **Total:** ₹{total_price}\n• **Dirección:** {address}\n• **Fecha:** {date}"
    },
    'STATUS_Pending': {
        'en': "⏳ Pending confirmation",
        'hi': "⏳ पुष्टि की प्रतीक्षा है",
        'es': "⏳ Pendiente de confirmación"
    },
    'STATUS_Preparing': {
        'en': "🍳 In the kitchen being prepared",
        'hi': "🍳 रसोई में तैयार किया जा रहा है",
        'es': "🍳 En la cocina preparándose"
    },
    'STATUS_Out_for_Delivery': {
        'en': "🛵 Out for delivery!",
        'hi': "🛵 डिलीवरी के लिए निकल चुका है!",
        'es': "🛵 ¡En camino para entrega!"
    },
    'STATUS_Delivered': {
        'en': "✅ Delivered safely!",
        'hi': "✅ सफलतापूर्वक डिलीवर हो गया!",
        'es': "✅ ¡Entregado con éxito!"
    },
    'CART_SUMMARY': {
        'en': "🛒 **Your Cart ({count} items):**\n\n{items_list}\n\n**Total:** ₹{total} 💳",
        'hi': "🛒 **आपकी कार्ट ({count} वस्तुएं):**\n\n{items_list}\n\n**कुल योग:** ₹{total} 💳",
        'es': "🛒 **Tu Carrito ({count} artículos):**\n\n{items_list}\n\n**Total:** ₹{total} 💳"
    },
    'CART_EMPTY': {
        'en': "Your cart is currently empty! 🛒 Let me recommend some tasty food to get started:",
        'hi': "आपकी कार्ट अभी खाली है! 🛒 शुरुआत करने के लिए मैं कुछ स्वादिष्ट व्यंजनों की सिफारिश करता हूँ:",
        'es': "¡Tu carrito está vacío! 🛒 Te recomiendo opciones deliciosas para empezar:"
    },
    'CART_CLEARED': {
        'en': "🗑️ Your cart has been emptied! Ready for a fresh start? What can I get for you?",
        'hi': "🗑️ आपकी कार्ट खाली कर दी गई है! नए सिरे से शुरुआत करें? मैं आपके लिए क्या ला सकता हूँ?",
        'es': "🗑️ ¡Tu carrito ha sido vaciado! ¿Listo para empezar de nuevo? ¿Qué deseas ordenar?"
    },
    'RECOMMEND_HEADER': {
        'en': "Here are our customer favorites and chef's top recommendations today! 🌟",
        'hi': "यहाँ आज के हमारे सबसे लोकप्रिय व्यंजन और शेफ़ की विशेष सिफारिशें हैं! 🌟",
        'es': "¡Aquí tienes los platos favoritos de los clientes y las recomendaciones del chef hoy! 🌟"
    },
    'PIZZA_HEADER': {
        'en': "🍕 Here are our freshly baked pizzas! Click **+ Add** to order:",
        'hi': "🍕 यहाँ हमारे ताज़ा बेक किए गए पिज़्ज़ा हैं! ऑर्डर करने के लिए **+ जोड़ें** पर क्लिक करें:",
        'es': "🍕 ¡Aquí están nuestras pizzas recién horneadas! Haz clic en **+ Añadir** para ordenar:"
    },
    'BURGER_HEADER': {
        'en': "🍔 Check out our juicy, handcrafted burgers! Click **+ Add** to order:",
        'hi': "🍔 हमारे स्वादिष्ट और रसीले बर्गर देखें! ऑर्डर करने के लिए **+ जोड़ें** पर क्लिक करें:",
        'es': "🍔 ¡Mira nuestras jugosas hamburguesas artesanales! Haz clic en **+ Añadir** para ordenar:"
    },
    'DESSERT_HEADER': {
        'en': "🍰 Save room for dessert! Here are our mouth-watering sweet treats:",
        'hi': "🍰 मीठे के लिए जगह बचाएँ! यहाँ हमारे स्वादिष्ट डेज़र्ट हैं:",
        'es': "🍰 ¡Guarda espacio para el postre! Aquí tienes nuestros deliciosos dulces:"
    },
    'VEG_HEADER': {
        'en': "🥗 Here are our popular 100% vegetarian dishes! Click **+ Add** to order:",
        'hi': "🥗 यहाँ हमारे लोकप्रिय 100% शाकाहारी व्यंजन हैं! ऑर्डर करने के लिए **+ जोड़ें** पर क्लिक करें:",
        'es': "🥗 ¡Aquí tienes nuestros platos 100% vegetarianos populares! Haz clic en **+ Añadir**:"
    },
    'NONVEG_HEADER': {
        'en': "🍗 Here are our delicious non-veg customer favorites! Click **+ Add** to order:",
        'hi': "🍗 यहाँ हमारे स्वादिष्ट मांसाहारी व्यंजन हैं! ऑर्डर करने के लिए **+ जोड़ें** पर क्लिक करें:",
        'es': "🍗 ¡Aquí tienes nuestros deliciosos platos no vegetarianos favoritos! Haz clic en **+ Añadir**:"
    },
    'SEARCH_FOUND': {
        'en': "Found **{item_name}**! 🍽️ Click **+ Add** to order:",
        'hi': "**{item_name}** मिल गया! 🍽️ ऑर्डर करने के लिए **+ जोड़ें** पर क्लिक करें:",
        'es': "¡Se encontró **{item_name}**! 🍽️ Haz clic en **+ Añadir** para ordenar:"
    },
    'DELIVERY_TIME': {
        'en': "⏱️ Our average delivery time is **30-45 minutes**! Hot, fresh, and straight to your door. 🚴",
        'hi': "⏱️ हमारा औसत डिलीवरी समय **30-45 मिनट** है! गरमा-गरम और ताज़ा खाना सीधे आपके घर तक। 🚴",
        'es': "⏱️ ¡Nuestro tiempo promedio de entrega es de **30-45 minutos**! Caliente, fresco y directo a tu puerta. 🚴"
    },
    'FALLBACK': {
        'en': "I'm not quite sure I caught that. Would you like to explore our menu or ask for recommendations? 🍕",
        'hi': "मैं इसे पूरी तरह समझ नहीं पाया। क्या आप हमारा मेनू देखना चाहेंगे या सिफारिशें मांगना चाहेंगे? 🍕",
        'es': "No entendí muy bien. ¿Te gustaría explorar nuestro menú o pedir recomendaciones? 🍕"
    }
}

QUICK_REPLIES_BY_LANG = {
    'en': {
        'default': ["🌟 Top Picks", "🍕 Pizzas", "🍔 Burgers", "🌱 Veg Only", "📦 Track Order", "🛒 My Cart"],
        'cart': ["View Cart 🛒", "Proceed to Checkout 💳", "More Dishes 🍽️"],
        'order': ["Go to Profile Page 👤", "Order More Food 🍕", "View Cart 🛒"],
        'food': ["View Cart 🛒", "Checkout 💳", "Show Menu 🍽️"],
        'auth': ["Go to Login 🔑", "Browse Menu 🍽️"]
    },
    'hi': {
        'default': ["🌟 लोकप्रिय व्यंजन", "🍕 पिज़्ज़ा", "🍔 बर्गर", "🌱 शाकाहारी", "📦 ऑर्डर ट्रैक करें", "🛒 मेरी कार्ट"],
        'cart': ["कार्ट देखें 🛒", "चेकआउट 💳", "और व्यंजन देखें 🍽️"],
        'order': ["प्रोफ़ाइल पेज 👤", "और खाना ऑर्डर करें 🍕", "कार्ट देखें 🛒"],
        'food': ["कार्ट देखें 🛒", "चेकआउट 💳", "मेनू देखें 🍽️"],
        'auth': ["लॉगिन करें 🔑", "मेनू ब्राउज़ करें 🍽️"]
    },
    'es': {
        'default': ["🌟 Recomendados", "🍕 Pizzas", "🍔 Hamburguesas", "🌱 Vegetariano", "📦 Rastrear Pedido", "🛒 Mi Carrito"],
        'cart': ["Ver Carrito 🛒", "Finalizar Compra 💳", "Más Platos 🍽️"],
        'order': ["Ir a mi Perfil 👤", "Pedir Más Comida 🍕", "Ver Carrito 🛒"],
        'food': ["Ver Carrito 🛒", "Pagar 💳", "Ver Menú 🍽️"],
        'auth': ["Iniciar Sesión 🔑", "Explorar Menú 🍽️"]
    }
}

def t(key, lang='en', **kwargs):
    """Retrieve localized template string and format with kwargs."""
    lang = lang if lang in ('en', 'hi', 'es') else 'en'
    entry = TRANSLATIONS.get(key, {})
    template = entry.get(lang) or entry.get('en', '')
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template

def get_quick_replies(category='default', lang='en'):
    """Return localized quick reply chips."""
    lang = lang if lang in ('en', 'hi', 'es') else 'en'
    lang_replies = QUICK_REPLIES_BY_LANG.get(lang, QUICK_REPLIES_BY_LANG['en'])
    return lang_replies.get(category, lang_replies['default'])
