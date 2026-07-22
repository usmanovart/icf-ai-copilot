import { ConsentGate } from "@/components/assessment/ConsentGate";
import { AssessmentFlow } from "@/components/assessment/AssessmentFlow";

export default function AssessmentPage() {
  return (
    <div className="p-6 md:p-8">
      <ConsentGate>
        <AssessmentFlow />
      </ConsentGate>
    </div>
  );
}
