interface MasteryBadgeProps {
  score: number | null;
  size?: "sm" | "md" | "lg";
}

export default function MasteryBadge({ score, size = "md" }: MasteryBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span className={`inline-flex items-center rounded-full bg-gray-100 text-gray-600 font-medium ${sizeClasses(size)}`}>
        Not started
      </span>
    );
  }

  let color = "bg-red-100 text-red-700";
  let label = "Needs review";

  if (score >= 80) {
    color = "bg-green-100 text-green-700";
    label = "Mastered";
  } else if (score >= 60) {
    color = "bg-blue-100 text-blue-700";
    label = "Proficient";
  } else if (score >= 30) {
    color = "bg-yellow-100 text-yellow-700";
    label = "In progress";
  }

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${color} ${sizeClasses(size)}`}>
      {Math.round(score)}% - {label}
    </span>
  );
}

function sizeClasses(size: "sm" | "md" | "lg") {
  switch (size) {
    case "sm": return "px-2 py-0.5 text-xs";
    case "md": return "px-2.5 py-1 text-sm";
    case "lg": return "px-3 py-1.5 text-base";
  }
}
