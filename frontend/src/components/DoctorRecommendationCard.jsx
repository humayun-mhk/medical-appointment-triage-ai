import { formatCurrency, formatDateTime } from "../utils/format.js";
import Button from "./Button.jsx";
import Card, { CardBody } from "./Card.jsx";
import DoctorPortrait from "./DoctorPortrait.jsx";
import ScoreBreakdown from "./ScoreBreakdown.jsx";

export default function DoctorRecommendationCard({ recommendation, onBook, isBooking }) {
  return (
    <Card>
      <CardBody className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex gap-3">
            <DoctorPortrait doctor={recommendation} className="h-20 w-20" />
            <div>
              <h2 className="text-lg font-semibold text-gray-950">{recommendation.doctor_name}</h2>
              <p className="text-sm font-medium text-teal-700">{recommendation.specialty}</p>
              <p className="mt-1 text-sm text-gray-500">{recommendation.clinic_address}</p>
            </div>
          </div>
          <div className="text-left sm:text-right">
            <p className="text-2xl font-bold text-gray-950">{recommendation.score}</p>
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">match score</p>
          </div>
        </div>
        {recommendation.emergency_warning && (
          <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {recommendation.emergency_warning}
          </div>
        )}
        <p className="text-sm leading-6 text-gray-600">{recommendation.reason}</p>
        <div className="grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <span className="block text-gray-500">Next slot</span>
            <span className="font-semibold text-gray-900">{formatDateTime(recommendation.next_available_slot?.start_time)}</span>
          </div>
          <div>
            <span className="block text-gray-500">Fee</span>
            <span className="font-semibold text-gray-900">{formatCurrency(recommendation.consultation_fee)}</span>
          </div>
          <div>
            <span className="block text-gray-500">Rating</span>
            <span className="font-semibold text-gray-900">{recommendation.rating} ({recommendation.total_reviews})</span>
          </div>
        </div>
        <ScoreBreakdown breakdown={recommendation.score_breakdown} />
        <Button className="w-full" onClick={() => onBook(recommendation)} isLoading={isBooking}>
          Book This Slot
        </Button>
      </CardBody>
    </Card>
  );
}
