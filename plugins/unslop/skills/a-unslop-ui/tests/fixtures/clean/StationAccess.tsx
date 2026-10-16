import { MapPin, Accessibility } from "lucide-react";

export function StationAccess() {
  return (
    <section aria-labelledby="access-title">
      <h2 id="access-title">Find the entrance</h2>
      <div className="flex gap-3">
        <span className="rounded-lg bg-primary/10"><MapPin aria-hidden="true" /></span>
        <p>The main entrance faces Station Square.</p>
      </div>
      <div className="flex gap-3">
        <span className="rounded-lg bg-primary/10"><Accessibility aria-hidden="true" /></span>
        <p>Step-free access is beside the ticket office.</p>
      </div>
      <a href="/station-map">View station map →</a>
    </section>
  );
}
