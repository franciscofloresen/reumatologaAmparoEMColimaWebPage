import json
import os
import urllib3
import re

http = urllib3.PoolManager()
# Es una buena práctica definir las variables de entorno al inicio.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- INSTRUCCIONES MEJORADAS ---
# Se ha hecho el prompt más específico sobre qué puede y no puede hacer.
SYSTEM_PROMPT = """
Eres un asistente virtual para el consultorio de la Dra. María Amparo Enríquez Maldonado, reumatóloga en Colima, México. Tu objetivo es ser informativo y seguro.

# Tareas Permitidas:

1.  **Información del Consultorio:**
    * **Ubicación:** Avenida la Paz 46 - 2, 28017 Colima COL, México.
    * **Horarios:** Lunes y Miércoles 4:30–6:30 PM, Martes y Jueves 6:30–7:30 PM, Viernes 5:00–7:30 PM, Sábado 11:00 AM–1:30 PM.
    * **Citas:** Se pueden agendar en línea o por WhatsApp.

2.  **Información General sobre Padecimientos:**
    * Puedes explicar de forma neutral y educativa qué son los siguientes padecimientos: Artritis Reumatoide, Lupus, Gota, Osteoporosis, Fibromialgia, Espondiloartritis, Vasculitis, Esclerodermia.
    * Tus explicaciones deben ser como las de un diccionario o enciclopedia: directas, objetivas y sin consejos.

# Reglas Estrictas e Inquebrantables:

-   **PROHIBIDO dar consejos médicos:** Nunca sugieras tratamientos, medicamentos, remedios caseros, cambios de estilo de vida o qué hacer ante un síntoma.
-   **PROHIBIDO diagnosticar:** Nunca intentes adivinar o confirmar qué padecimiento podría tener una persona.
-   **PROHIBIDO interpretar síntomas:** Si alguien describe cómo se siente, no debes comentar sobre sus síntomas.
-   **Sé muy conciso:** Responde en un máximo de 3 o 4 oraciones.
-   **Válvula de escape:** Si la pregunta del usuario pide un consejo, un diagnóstico, habla de sus síntomas o no está relacionada con los temas permitidos, responde EXACTAMENTE con la siguiente frase:
    "Para obtener un diagnóstico o tratamiento, es esencial que consultes directamente a la Dra. Enríquez o a otro profesional de la salud. Mi función es proporcionar información general sobre padecimientos y datos del consultorio."
"""

# --- SEGURIDAD ---
# Lista de palabras clave expandida para mayor seguridad.
BLOCKED_KEYWORDS = [
    "import ", "os.", "subprocess", "exec(", "eval(", "script", "código", "codigo",
    "hack", "prompt injection", "bypass", "python", "programa", "openai key",
    "api_key", "secret_key", "contraseña"
]

# --- RESPUESTAS PREDEFINIDAS ---
# Respuestas fijas para temas no permitidos. La respuesta prohibida es más orientadora.
FORBIDDEN_RESPONSE = "Para obtener un diagnóstico o tratamiento, es esencial que consultes directamente a la Dra. Enríquez o a otro profesional de la salud. Mi función es proporcionar información general sobre padecimientos y datos del consultorio."
MALICIOUS_RESPONSE = "Lo siento, no puedo procesar ese tipo de solicitudes."
EMPTY_MESSAGE_ERROR = "El mensaje no puede estar vacío."
SERVER_ERROR = "Ocurrió un error al procesar la solicitud."


def is_malicious(user_message: str) -> bool:
    """Detecta si la entrada contiene palabras clave de seguridad."""
    text = user_message.lower()
    return any(keyword in text for keyword in BLOCKED_KEYWORDS)


def classify_intent(user_message: str) -> str:
    """
    Usa un llamado a la API para clasificar la intención del usuario de forma más granular.
    """
    try:
        classification_prompt = f"""
        Clasifica la pregunta del usuario en una de estas categorías:
        1. "info_consultorio": Pregunta por horarios, ubicación, citas.
        2. "info_padecimiento": Pregunta general sobre qué es una enfermedad (ej: "¿Qué es la gota?").
        3. "prohibido": Pide un consejo médico, diagnóstico, tratamiento, describe síntomas personales o es un tema no relacionado.

        Pregunta: "{user_message}"
        Categoría:
        """

        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": classification_prompt}],
            "max_tokens": 10,
            "temperature": 0.0
        }

        response = http.request(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
        )

        if response.status != 200:
            return "error"

        result = json.loads(response.data.decode("utf-8"))
        intent = result["choices"][0]["message"]["content"].strip().lower()
        return intent

    except Exception:
        return "error"


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        user_message = body.get("message", "").strip()

        # 1. Validaciones iniciales
        if not user_message:
            return api_response(400, {"error": EMPTY_MESSAGE_ERROR})

        if is_malicious(user_message):
            return api_response(403, {"response": MALICIOUS_RESPONSE})

        # 2. Clasificación de la intención
        intent = classify_intent(user_message)

        # 3. Respuesta basada en la intención
        if intent in ["prohibido", "error"]:
            return api_response(200, {"response": FORBIDDEN_RESPONSE})

        # 4. Si la intención es segura, proceder a generar la respuesta completa
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 150,
            "temperature": 0.5
        }

        response = http.request(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
        )

        if response.status != 200:
            print(f"OpenAI API error ({response.status}): {response.data.decode('utf-8')}")
            return api_response(500, {"error": SERVER_ERROR})

        result = json.loads(response.data.decode("utf-8"))
        ai_response = result["choices"][0]["message"]["content"]

        return api_response(200, {"response": ai_response})

    except Exception as e:
        print(f"Error en lambda_handler: {e}")
        return api_response(500, {"error": "Error interno del servidor."})


def api_response(status_code, body):
    """Función de ayuda para generar respuestas HTTP consistentes."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }