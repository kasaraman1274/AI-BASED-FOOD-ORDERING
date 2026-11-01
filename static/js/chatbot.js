$(document).ready(function() {
    // Multilingual configuration
    const LANG_CONFIG = {
        'en': {
            voice_lang: 'en-US',
            placeholder: 'Ask about dishes, orders, prices...',
            listening: 'Listening to your voice...',
            btn_add: '+ Add',
            welcome: "👋 Hi there! I'm your <strong>AI Food Assistant</strong>.<br>Craving pizza, burgers, or want to track an order? I can recommend dishes and add them directly to your cart!",
            cleared: "Chat cleared! 👋 How can I help you? Ask about dishes, orders, or your cart!",
            quick_replies: ["🌟 Top Picks", "🍕 Pizzas", "🍔 Burgers", "🌱 Veg Only", "📦 Track Order", "🛒 My Cart"]
        },
        'hi': {
            voice_lang: 'hi-IN',
            placeholder: 'व्यंजन, ऑर्डर या दाम के बारे में पूछें...',
            listening: 'आपकी आवाज़ सुन रहा हूँ...',
            btn_add: '+ जोड़ें',
            welcome: "👋 नमस्ते! मैं आपका <strong>AI फ़ूड असिस्टेंट</strong> हूँ।<br>क्या आप पिज़्ज़ा, बर्गर खाना चाहते हैं या ऑर्डर ट्रैक करना चाहते हैं? मैं आपके लिए पसंदीदा व्यंजन ढूँढ सकता हूँ!",
            cleared: "चैट साफ़ हो गई! 👋 मैं आपकी क्या मदद करूँ? व्यंजन, ऑर्डर या अपनी कार्ट के बारे में पूछें!",
            quick_replies: ["🌟 लोकप्रिय व्यंजन", "🍕 पिज़्ज़ा", "🍔 बर्गर", "🌱 शाकाहारी", "📦 ऑर्डर ट्रैक करें", "🛒 मेरी कार्ट"]
        },
        'es': {
            voice_lang: 'es-ES',
            placeholder: 'Pregunta sobre platos, pedidos, precios...',
            listening: 'Escuchando tu voz...',
            btn_add: '+ Añadir',
            welcome: "👋 ¡Hola! Soy tu <strong>Asistente de Comida IA</strong>.<br>¿Se te apetece pizza, hamburguesas o deseas rastrear tu pedido? ¡Puedo sugerirte platos y añadirlos a tu carrito!",
            cleared: "¡Chat vaciado! 👋 ¿En qué te ayudo? Pregunta sobre comida, pedidos o tu carrito.",
            quick_replies: ["🌟 Recomendados", "🍕 Pizzas", "🍔 Hamburguesas", "🌱 Vegetariano", "📦 Rastrear Pedido", "🛒 Mi Carrito"]
        }
    };

    // Determine initial language
    let siteLang = ($('#site-active-lang').data('lang') || 'en').toLowerCase();
    if (!LANG_CONFIG[siteLang]) siteLang = 'en';

    let currentLang = localStorage.getItem('ai_foodie_chat_lang') || siteLang;
    if (!LANG_CONFIG[currentLang]) currentLang = 'en';

    $('#chat-lang-select').val(currentLang);
    applyLanguageUI(currentLang, false);

    // State management
    let ttsEnabled = localStorage.getItem('ai_foodie_tts_enabled') === 'true';
    updateTtsIcon();

    // Language Change Event
    $('#chat-lang-select').change(function() {
        currentLang = $(this).val();
        localStorage.setItem('ai_foodie_chat_lang', currentLang);
        applyLanguageUI(currentLang, true);
    });

    function applyLanguageUI(lang, showGreeting) {
        const conf = LANG_CONFIG[lang] || LANG_CONFIG['en'];
        $('#chat-input').attr('placeholder', conf.placeholder);
        setQuickReplies(conf.quick_replies);

        if (showGreeting) {
            appendBotMessage(conf.welcome, [], conf.quick_replies, conf.btn_add);
        }
    }

    // Toggle Chatbot
    $('#chatbot-toggle, #close-chat').click(function() {
        $('#chatbot-widget').fadeToggle(200, function() {
            if ($('#chatbot-widget').is(':visible')) {
                $('#chat-unread-dot').hide();
                $('#chat-input').focus();
                scrollChatToBottom();
            }
        });
    });

    // TTS Voice Toggle
    $('#tts-toggle').click(function() {
        ttsEnabled = !ttsEnabled;
        localStorage.setItem('ai_foodie_tts_enabled', ttsEnabled);
        updateTtsIcon();
        if (ttsEnabled) {
            const prompt = currentLang === 'hi' ? "आवाज़ प्रतिक्रिया चालू हो गई है!" : (currentLang === 'es' ? "¡Respuesta de voz activada!" : "Voice response enabled!");
            speak(prompt, currentLang);
        } else {
            if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        }
    });

    function updateTtsIcon() {
        $('#tts-icon').text(ttsEnabled ? '🔊' : '🔇');
        $('#tts-toggle').attr('title', ttsEnabled ? 'Voice Response: ON' : 'Voice Response: OFF');
    }

    // Clear Chat
    $('#clear-chat').click(function() {
        const conf = LANG_CONFIG[currentLang] || LANG_CONFIG['en'];
        $('#chat-messages').html(`
            <div class="chat-message-row bot-row mb-3">
                <div class="msg-avatar bot-avatar">🤖</div>
                <div class="msg-content">
                    <div class="bot-msg shadow-sm">${conf.cleared}</div>
                </div>
            </div>
        `);
        setQuickReplies(conf.quick_replies);
    });

    // Enter Key to Send
    $('#chat-input').keypress(function(e) {
        if (e.which === 13) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send Button Click
    $('#send-btn').click(function() {
        sendMessage();
    });

    // Quick Reply Chip Click (delegated)
    $(document).on('click', '.quick-reply-chip', function() {
        const text = $(this).data('msg') || $(this).text().trim();
        if (text) {
            sendMessage(text);
        }
    });

    // Direct Add to Cart from Chat Cards (delegated)
    $(document).on('click', '.chat-add-btn', function() {
        const btn = $(this);
        const itemId = btn.data('item-id');
        if (!itemId || btn.hasClass('added')) return;

        btn.prop('disabled', true).text('...');

        $.ajax({
            url: '/api/chat/add-to-cart/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ item_id: itemId, quantity: 1, lang: currentLang }),
            success: function(res) {
                btn.removeClass('chat-add-btn').addClass('chat-add-btn added').text('✓');
                if (res.cart_count !== undefined) {
                    updateNavbarCart(res.cart_count);
                }
                const conf = LANG_CONFIG[currentLang] || LANG_CONFIG['en'];
                appendBotMessage(res.message, [], conf.quick_replies);
            },
            error: function() {
                btn.prop('disabled', false).text('+');
                appendBotMessage("⚠️ Could not add item to cart. Please try again or check the menu.");
            }
        });
    });

    function sendMessage(customText) {
        let text = customText !== undefined ? customText : $('#chat-input').val().trim();
        if (text === '') return;

        appendUserMessage(text);
        if (customText === undefined) {
            $('#chat-input').val('');
        }

        // Show typing indicator
        $('#chat-typing').show();
        scrollChatToBottom();

        $.ajax({
            url: '/api/chat/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: text, lang: currentLang }),
            success: function(res) {
                $('#chat-typing').hide();

                // If backend detected a different language, sync it
                if (res.lang && res.lang !== currentLang && LANG_CONFIG[res.lang]) {
                    currentLang = res.lang;
                    $('#chat-lang-select').val(currentLang);
                    localStorage.setItem('ai_foodie_chat_lang', currentLang);
                }

                const btnAddText = res.btn_add_text || (LANG_CONFIG[currentLang] || LANG_CONFIG['en']).btn_add;
                appendBotMessage(res.response, res.items || [], res.quick_replies || [], btnAddText);

                if (res.cart_count !== undefined) {
                    updateNavbarCart(res.cart_count);
                }

                if (ttsEnabled && res.response) {
                    const speechText = res.response.replace(/\*\*/g, '').replace(/[•\n]/g, ' ');
                    speak(speechText, currentLang);
                }

                if (res.action) {
                    handleAction(res.action);
                }
            },
            error: function() {
                $('#chat-typing').hide();
                appendBotMessage("Sorry, I'm having trouble connecting to the food service right now. Please try again! 🍽️");
            }
        });
    }

    function appendUserMessage(text) {
        const escaped = $('<div>').text(text).html();
        const html = `
            <div class="chat-message-row user-row mb-3">
                <div class="msg-avatar user-avatar">👤</div>
                <div class="msg-content">
                    <div class="user-msg shadow-sm">${escaped}</div>
                </div>
            </div>
        `;
        $('#chat-messages').append(html);
        scrollChatToBottom();
    }

    function appendBotMessage(rawText, items, quickReplies, btnAddText) {
        let formattedText = formatMarkdown(rawText);
        const addLabel = btnAddText || (LANG_CONFIG[currentLang] || LANG_CONFIG['en']).btn_add;

        let cardsHtml = '';
        if (items && items.length > 0) {
            cardsHtml = '<div class="chat-food-cards">';
            items.forEach(function(item) {
                const imgTag = item.image_url ? `<img src="${item.image_url}" class="chat-card-thumb" alt="${item.name}">` : '';
                cardsHtml += `
                    <div class="chat-food-card">
                        ${imgTag}
                        <div class="chat-card-info">
                            <div class="chat-card-title">${item.name}</div>
                            <div class="chat-card-price">₹${parseFloat(item.price).toFixed(2)}</div>
                        </div>
                        <button class="chat-add-btn" data-item-id="${item.id}">${addLabel}</button>
                    </div>
                `;
            });
            cardsHtml += '</div>';
        }

        const html = `
            <div class="chat-message-row bot-row mb-3">
                <div class="msg-avatar bot-avatar">🤖</div>
                <div class="msg-content">
                    <div class="bot-msg shadow-sm">
                        ${formattedText}
                        ${cardsHtml}
                    </div>
                </div>
            </div>
        `;
        $('#chat-messages').append(html);
        scrollChatToBottom();

        if (quickReplies && quickReplies.length > 0) {
            setQuickReplies(quickReplies);
        }
    }

    function setQuickReplies(replies) {
        let html = '';
        replies.forEach(function(r) {
            const clean = $('<div>').text(r).html();
            html += `<button class="quick-reply-chip" data-msg="${clean}">${clean}</button>`;
        });
        $('#chat-quick-replies').html(html);
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let escaped = $('<div>').text(text).html();
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
        escaped = escaped.replace(/• (.*?)(?=(\n|$))/g, '<div class="ms-2">🔹 $1</div>');
        escaped = escaped.replace(/\n/g, '<br>');
        return escaped;
    }

    function updateNavbarCart(count) {
        const badge = $('#nav-cart-badge');
        if (count > 0) {
            badge.text(count).show();
        } else {
            badge.hide();
        }
    }

    function scrollChatToBottom() {
        const container = document.getElementById('chat-messages');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    function handleAction(action) {
        setTimeout(function() {
            if (action === 'MENU_REDIRECT') {
                window.location.href = '/menu/';
            } else if (action === 'FILTER_VEG') {
                window.location.href = '/menu/?q=veg';
            } else if (action === 'FILTER_NONVEG') {
                window.location.href = '/menu/?q=non-veg';
            } else if (action === 'FILTER_PIZZA') {
                window.location.href = '/menu/?category=pizza';
            } else if (action === 'FILTER_BURGER') {
                window.location.href = '/menu/?category=burger';
            } else if (action === 'FILTER_DESSERT') {
                window.location.href = '/menu/?category=desserts';
            } else if (action === 'CHECKOUT_REDIRECT') {
                window.location.href = '/checkout/';
            } else if (action === 'LOGIN_REDIRECT') {
                window.location.href = '/login/';
            }
        }, 1800);
    }

    // --- Multilingual Voice Ordering (Web Speech API) ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let isRecording = false;

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = function() {
            isRecording = true;
            const conf = LANG_CONFIG[currentLang] || LANG_CONFIG['en'];
            $('#voice-btn').addClass('recording').attr('title', 'Listening...');
            $('#chat-input').attr('placeholder', conf.listening);
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            $('#chat-input').val(transcript);
            sendMessage(transcript);
        };

        recognition.onerror = function(event) {
            console.warn("Speech recognition error:", event.error);
            stopRecording();
        };

        recognition.onend = function() {
            stopRecording();
        };

        function stopRecording() {
            isRecording = false;
            const conf = LANG_CONFIG[currentLang] || LANG_CONFIG['en'];
            $('#voice-btn').removeClass('recording').attr('title', 'Voice Order');
            $('#chat-input').attr('placeholder', conf.placeholder);
            try { recognition.stop(); } catch(e) {}
        }

        $('#voice-btn').click(function() {
            if (isRecording) {
                stopRecording();
            } else {
                try {
                    const conf = LANG_CONFIG[currentLang] || LANG_CONFIG['en'];
                    recognition.lang = conf.voice_lang; // Set to 'hi-IN', 'es-ES', or 'en-US'
                    recognition.start();
                } catch(e) {
                    console.error("Recognition start error:", e);
                }
            }
        });
    } else {
        $('#voice-btn').hide();
    }

    // Multilingual Text-to-Speech
    function speak(text, lang) {
        if ('speechSynthesis' in window && ttsEnabled) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            const conf = LANG_CONFIG[lang] || LANG_CONFIG['en'];
            utterance.lang = conf.voice_lang;
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    }
});
