export class Analytics {
  constructor(_config: Record<string, unknown> = {}) {}

  track(_event: unknown): void {
    // telemetry disabled: no-op
  }

  flush(_callback?: (err?: Error) => void): void {
    _callback?.();
  }
}

export default Analytics;
