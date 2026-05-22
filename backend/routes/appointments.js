const express = require('express');
const Joi = require('joi');
const database = require('../database');

const router = express.Router();

// Validation schema
const appointmentSchema = Joi.object({
    firstName: Joi.string().min(2).max(50).required(),
    lastName: Joi.string().min(2).max(50).required(),
    phone: Joi.string().pattern(/^[0-9+\-\s()]+$/).min(10).required(),
    email: Joi.string().email().optional().allow(''),
    preferredDate: Joi.date().min('now').required(),
    preferredTime: Joi.string().pattern(/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/).required(),
    reason: Joi.string().max(500).optional().allow(''),
    consultationType: Joi.string().valid('primera-vez', 'seguimiento', 'urgente').required()
});

// Create new appointment
router.post('/', async (req, res) => {
    try {
        const { error, value } = appointmentSchema.validate(req.body);
        if (error) {
            return res.status(400).json({ 
                error: 'Datos inválidos', 
                details: error.details[0].message 
            });
        }

        const appointment = await database.createAppointment(value);
        res.status(201).json(appointment);
    } catch (error) {
        console.error('Error creating appointment:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Get all appointments
router.get('/', async (req, res) => {
    try {
        const appointments = await database.getAllAppointments();
        res.json(appointments);
    } catch (error) {
        console.error('Error fetching appointments:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Get appointment by ID
router.get('/:id', async (req, res) => {
    try {
        const appointment = await database.getAppointmentById(req.params.id);
        if (!appointment) {
            return res.status(404).json({ error: 'Cita no encontrada' });
        }
        res.json(appointment);
    } catch (error) {
        console.error('Error fetching appointment:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Update appointment
router.put('/:id', async (req, res) => {
    try {
        const updateSchema = Joi.object({
            status: Joi.string().valid('pending', 'confirmed', 'completed', 'cancelled').optional(),
            firstName: Joi.string().min(2).max(50).optional(),
            lastName: Joi.string().min(2).max(50).optional(),
            phone: Joi.string().pattern(/^[0-9+\-\s()]+$/).min(10).optional(),
            email: Joi.string().email().optional().allow(''),
            preferredDate: Joi.date().optional(),
            preferredTime: Joi.string().pattern(/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/).optional(),
            reason: Joi.string().max(500).optional().allow(''),
            consultationType: Joi.string().valid('primera-vez', 'seguimiento', 'urgente').optional()
        });

        const { error, value } = updateSchema.validate(req.body);
        if (error) {
            return res.status(400).json({ 
                error: 'Datos inválidos', 
                details: error.details[0].message 
            });
        }

        const appointment = await database.updateAppointment(req.params.id, value);
        if (!appointment) {
            return res.status(404).json({ error: 'Cita no encontrada' });
        }

        res.json(appointment);
    } catch (error) {
        console.error('Error updating appointment:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

// Delete appointment
router.delete('/:id', async (req, res) => {
    try {
        const deleted = await database.deleteAppointment(req.params.id);
        if (!deleted) {
            return res.status(404).json({ error: 'Cita no encontrada' });
        }
        res.json({ message: 'Cita eliminada correctamente' });
    } catch (error) {
        console.error('Error deleting appointment:', error);
        res.status(500).json({ error: 'Error interno del servidor' });
    }
});

module.exports = router;
