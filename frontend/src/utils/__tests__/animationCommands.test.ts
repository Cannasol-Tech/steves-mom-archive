import { parseAnimationFromText } from '../animationCommands';

describe('animationCommands parser', () => {
  test('parses HTML comment envelope', () => {
    const text = `Here we go <!-- smom:{"action":"dance","side":"right","intensity":"high"} --> darling`;
    const cmd = parseAnimationFromText(text)!;
    expect(cmd).toBeTruthy();
    expect(cmd.action).toBe('dance');
    expect(cmd.side).toBe('right');
    expect(cmd.intensity).toBe('high');
  });

  test('parses JSON block', () => {
    const text = 'Some reply {"type":"smom","action":"wink","side":"left"}';
    const cmd = parseAnimationFromText(text)!;
    expect(cmd).toBeTruthy();
    expect(cmd.action).toBe('wink');
    expect(cmd.side).toBe('left');
  });

  test('parses DSL tag', () => {
    const text = 'Okay [smom action=blow-kiss side=left intensity=low] sweetie';
    const cmd = parseAnimationFromText(text)!;
    expect(cmd).toBeTruthy();
    expect(cmd.action).toBe('blow-kiss');
    expect(cmd.side).toBe('left');
    expect(cmd.intensity).toBe('low');
  });

  test('returns null when not found', () => {
    const text = 'Just a plain message with no directives';
    const cmd = parseAnimationFromText(text);
    expect(cmd).toBeNull();
  });
});

