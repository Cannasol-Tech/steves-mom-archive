import { characterController, type AnimationAction, type CharacterSide } from '../components/Character/StevesMomCharacter';

export type AnimationCommand = {
  action?: AnimationAction;
  side?: CharacterSide;
  intensity?: 'low' | 'medium' | 'high';
};

// Parse a minimal JSON envelope in assistant replies or websocket messages, e.g.:
// <!-- smom:{"action":"dance","side":"right","intensity":"high"} -->
// or a raw JSON line: {"type":"smom","action":"wink","side":"left"}
export function parseAnimationFromText(text: string): AnimationCommand | null {
  try {
    // HTML comment envelope
    const commentMatch = text.match(/smom:\s*\{[^}]*\}/i);
    if (commentMatch) {
      const jsonStr = commentMatch[0].replace(/^[^\{]*/, '');
      const cmd = JSON.parse(jsonStr);
      if (cmd && typeof cmd === 'object') return normalize(cmd);
    }
  } catch {}

  try {
    // Look for standalone JSON blocks
    const jsonMatch = text.match(/\{\s*"type"\s*:\s*"smom"[^}]*\}/i);
    if (jsonMatch) {
      const cmd = JSON.parse(jsonMatch[0]);
      return normalize(cmd);
    }
  } catch {}

  // Lightweight DSL: [smom action=dance side=right intensity=high]
  const dsl = text.match(/\[smom\s+([^\]]+)\]/i);
  if (dsl) {
    const params = Object.fromEntries(
      dsl[1]
        .split(/\s+/)
        .map(kv => kv.split('='))
        .map(([k, v]) => [k.trim(), v?.trim()])
    );
    return normalize(params as any);
  }

  return null;
}

export function executeAnimation(cmd: AnimationCommand): void {
  if (!cmd) return;
  if (cmd.side) characterController.set({ side: cmd.side });
  if (cmd.intensity) characterController.set({ intensity: cmd.intensity });
  if (cmd.action) characterController.set({ action: cmd.action });
}

function normalize(obj: any): AnimationCommand {
  const out: AnimationCommand = {};
  if (obj.action) out.action = String(obj.action) as AnimationAction;
  if (obj.side) {
    const side = String(obj.side).toLowerCase();
    out.side = (side === 'left' || side === 'right') ? (side as CharacterSide) : 'left';
  }
  if (obj.intensity) out.intensity = String(obj.intensity) as any;
  return out;
}

