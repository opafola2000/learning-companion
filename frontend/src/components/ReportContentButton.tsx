import { useState } from "react";
import { submitFeedback } from "../api/feedback";

interface Props {
  contentType: "topic" | "question" | "resource" | "curriculum";
  contentId: number;
}

export default function ReportContentButton({ contentType, contentId }: Props) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("outdated");
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  async function handleSubmit() {
    setStatus("sending");
    try {
      await submitFeedback({ content_type: contentType, content_id: contentId, reason, comment });
      setStatus("sent");
      setOpen(false);
    } catch {
      setStatus("error");
    }
  }

  if (status === "sent") {
    return <span className="text-xs text-green-600">Report submitted — thank you</span>;
  }

  return (
    <div className="inline-block">
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="text-xs text-gray-500 hover:text-red-600 underline"
        >
          Report issue
        </button>
      ) : (
        <div className="mt-2 p-3 bg-gray-50 border rounded-lg space-y-2">
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full text-xs border rounded px-2 py-1"
          >
            <option value="outdated">Outdated content</option>
            <option value="incorrect">Incorrect information</option>
            <option value="irrelevant">Not relevant to exam</option>
            <option value="other">Other</option>
          </select>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional details..."
            className="w-full text-xs border rounded px-2 py-1"
            rows={2}
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={status === "sending"}
              className="text-xs px-2 py-1 bg-red-600 text-white rounded"
            >
              Submit
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-xs px-2 py-1 border rounded"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
