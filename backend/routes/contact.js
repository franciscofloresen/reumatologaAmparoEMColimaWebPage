const express = require('express');
const nodemailer = require('nodemailer');
const Joi = require('joi');
const router = express.Router();

// Validación de datos
const contactSchema = Joi.object({
  name: Joi.string().min(2).max(100).required(),
  email: Joi.string().email().required(),
  phone: Joi.string().pattern(/^[0-9+\-\s()]+$/).min(10).max(20).required(),
  message: Joi.string().min(10).max(1000).required(),
  preferredContact: Joi.string().valid('email', 'phone', 'whatsapp').default('email')
});

// Configurar transporter de email (solo si las variables de entorno están configuradas)
let transporter = null;
if (process.env.EMAIL_USER && process.env.EMAIL_PASS) {
  transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS
    }
  });
}

// POST /api/contact - Enviar mensaje de contacto
router.post('/', async (req, res) => {
  try {
    const { error, value } = contactSchema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details[0].message });
    }

    const { name, email, phone, message, preferredContact } = value;

    // Log del mensaje (siempre funciona)
    console.log('Nuevo mensaje de contacto:', {
      name,
      email,
      phone,
      message,
      preferredContact,
      timestamp: new Date().toISOString()
    });

    // Si el transporter está configurado, enviar emails
    if (transporter) {
      try {
        // Email para la doctora
        const doctorEmail = {
          from: process.env.EMAIL_USER,
          to: process.env.DOCTOR_EMAIL || process.env.EMAIL_USER,
          subject: `Nuevo mensaje de contacto - ${name}`,
          html: `
            <h3>Nuevo mensaje de contacto</h3>
            <p><strong>Nombre:</strong> ${name}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Teléfono:</strong> ${phone}</p>
            <p><strong>Contacto preferido:</strong> ${preferredContact}</p>
            <p><strong>Mensaje:</strong></p>
            <p>${message}</p>
          `
        };

        // Email de confirmación para el paciente
        const patientEmail = {
          from: process.env.EMAIL_USER,
          to: email,
          subject: 'Mensaje recibido - Dra. María Amparo Enríquez',
          html: `
            <h3>Hola ${name},</h3>
            <p>Hemos recibido tu mensaje y nos pondremos en contacto contigo pronto.</p>
            <p>Gracias por tu interés en nuestros servicios.</p>
            <br>
            <p>Saludos cordiales,</p>
            <p>Dra. María Amparo Enríquez Maldonado</p>
          `
        };

        await transporter.sendMail(doctorEmail);
        await transporter.sendMail(patientEmail);
        
        res.json({ 
          success: true, 
          message: 'Mensaje enviado correctamente por email' 
        });
      } catch (emailError) {
        console.error('Error enviando email:', emailError);
        res.json({ 
          success: true, 
          message: 'Mensaje recibido (email no configurado)' 
        });
      }
    } else {
      res.json({ 
        success: true, 
        message: 'Mensaje recibido correctamente' 
      });
    }
  } catch (error) {
    console.error('Error procesando contacto:', error);
    res.status(500).json({ error: 'Error interno del servidor' });
  }
});

module.exports = router;
