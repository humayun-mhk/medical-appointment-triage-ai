import { z } from "zod";
import { commonEmailDomainMessage } from "../utils/emailValidation.js";

export const specialtySchema = z.object({
  name: z.string().min(2, "Specialty name is required"),
  description: z.string().optional(),
});

export const doctorSchema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  specialty_id: z.string().min(1, "Specialty is required"),
  qualification: z.string().min(2, "Qualification is required"),
  experience_years: z.coerce.number().min(0, "Experience cannot be negative"),
  bio: z.string().optional(),
  consultation_fee: z.coerce.number().min(0, "Fee cannot be negative"),
  clinic_address: z.string().min(2, "Clinic address is required"),
}).refine((data) => !commonEmailDomainMessage(data.email), {
  message: (data) => commonEmailDomainMessage(data.email),
  path: ["email"],
});

export const adminSlotSchema = z
  .object({
    doctor_id: z.string().min(1, "Doctor is required"),
    start_time: z.string().min(1, "Start time is required"),
    end_time: z.string().min(1, "End time is required"),
  })
  .refine((data) => new Date(data.start_time) < new Date(data.end_time), {
    message: "End time must be after start time",
    path: ["end_time"],
  });
