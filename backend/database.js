const fs = require('fs').promises;
const path = require('path');

const DB_FILE = path.join(__dirname, 'appointments.json');

class Database {
    constructor() {
        this.appointments = [];
        this.init();
    }

    async init() {
        try {
            const data = await fs.readFile(DB_FILE, 'utf8');
            this.appointments = JSON.parse(data);
        } catch (error) {
            // File doesn't exist, start with empty array
            this.appointments = [];
            await this.save();
        }
    }

    async save() {
        try {
            await fs.writeFile(DB_FILE, JSON.stringify(this.appointments, null, 2));
        } catch (error) {
            console.error('Error saving database:', error);
        }
    }

    generateId() {
        return Date.now().toString() + Math.random().toString(36).substr(2, 9);
    }

    async createAppointment(appointmentData) {
        const appointment = {
            id: this.generateId(),
            ...appointmentData,
            status: 'pending',
            createdAt: new Date().toISOString()
        };
        
        this.appointments.push(appointment);
        await this.save();
        return appointment;
    }

    async getAllAppointments() {
        return this.appointments.sort((a, b) => new Date(a.preferredDate) - new Date(b.preferredDate));
    }

    async getAppointmentById(id) {
        return this.appointments.find(apt => apt.id === id);
    }

    async updateAppointment(id, updates) {
        const index = this.appointments.findIndex(apt => apt.id === id);
        if (index === -1) return null;

        this.appointments[index] = { ...this.appointments[index], ...updates };
        await this.save();
        return this.appointments[index];
    }

    async deleteAppointment(id) {
        const index = this.appointments.findIndex(apt => apt.id === id);
        if (index === -1) return false;

        this.appointments.splice(index, 1);
        await this.save();
        return true;
    }
}

module.exports = new Database();
