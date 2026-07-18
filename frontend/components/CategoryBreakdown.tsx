import type { CategoryScore } from "@/lib/types";
import { scoreColorVar } from "@/lib/scoreColor";
import IssueCard from "./IssueCard";

export default function CategoryBreakdown({ categories }: { categories: CategoryScore[] }) {
  return (
    <div className="space-y-8">
      {categories.map((cat) => (
        <div key={cat.key}>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold">
              {cat.label}{" "}
              <span className="font-normal text-muted">({Math.round(cat.weight * 100)}% of score)</span>
            </h3>
            <span className="text-sm font-semibold" style={{ color: scoreColorVar(cat.score) }}>
              {Math.round(cat.score)}/100
            </span>
          </div>
          <div className="mb-3 h-2 w-full overflow-hidden rounded-full bg-surface">
            <div
              className="h-full rounded-full"
              style={{
                width: `${Math.round(cat.score)}%`,
                backgroundColor: scoreColorVar(cat.score),
              }}
            />
          </div>
          <div className="space-y-2">
            {cat.issues.map((issue) => (
              <IssueCard key={issue.id} issue={issue} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
