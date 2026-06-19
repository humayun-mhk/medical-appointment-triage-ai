import { z } from "zod";

export const patientProfileSchema = z.object({
  date_of_birth: z.string().optional(),
  gender: z.string().optional(),
  phone: z.string().optional(),
  address: z.string().optional(),
  blood_group: z.string().optional(),
  allergies: z.string().optional(),
  chronic_conditions: z.string().optional(),
  emergency_contact: z.string().optional(),
});

export const appointmentBookSchema = z.object({
  slot_id: z.string().min(1, "Select an available slot"),
  symptoms: z.string().optional(),
  patient_notes: z.string().optional(),
});
