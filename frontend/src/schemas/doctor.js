import { z } from "zod";

export const doctorNotesSchema = z.object({
  doctor_notes: z.string().min(1, "Doctor notes are required"),
});

export const availabilitySchema = z
  .object({
    start_time: z.string().min(1, "Start time is required"),
    end_time: z.string().min(1, "End time is required"),
  })
  .refine((data) => new Date(data.start_time) < new Date(data.end_time), {
    message: "End time must be after start time",
    path: ["end_time"],
  });
