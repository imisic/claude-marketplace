import { Zap, Shield, BarChart3 } from "lucide-react";

export function Features() {
  return <section>
    <div className="rounded-lg bg-primary/10"><Zap /></div>
    <div className="rounded-lg bg-primary/10"><Shield /></div>
    <div className="rounded-lg bg-blue-500/10"><BarChart3 /></div>
  </section>;
}
