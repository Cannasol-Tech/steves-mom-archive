import React, { useEffect, useMemo, useRef, useState } from 'react';

export type AnimationAction =
  | 'idle'
  | 'enter'
  | 'wink'
  | 'blow-kiss'
  | 'shimmy'
  | 'dance'
  | 'bounce'
  | 'point-left'
  | 'point-right';

export type CharacterSide = 'left' | 'right';

export type CharacterState = {
  side: CharacterSide;
  action: AnimationAction;
  intensity?: 'low' | 'medium' | 'high';
};

export type CharacterController = {
  subscribe: (cb: (state: CharacterState) => void) => () => void;
  set: (state: Partial<CharacterState>) => void;
  get: () => CharacterState;
};

// Lightweight global controller (no external deps)
const defaultState: CharacterState = { side: 'left', action: 'idle', intensity: 'medium' };
let currentState: CharacterState = { ...defaultState };
const subs = new Set<(s: CharacterState) => void>();

export const characterController: CharacterController = {
  subscribe: (cb) => {
    subs.add(cb);
    // initial emit
    cb(currentState);
    return () => subs.delete(cb);
  },
  set: (partial) => {
    currentState = { ...currentState, ...partial } as CharacterState;
    subs.forEach((cb) => cb(currentState));
  },
  get: () => currentState,
};

interface Props {
  size?: number; // px
}

const StevesMomCharacter: React.FC<Props> = ({ size = 140 }) => {
  const [state, setState] = useState<CharacterState>(characterController.get());
  const [isMirrored, setIsMirrored] = useState(false);
  const actionRef = useRef(state.action);

  useEffect(() => characterController.subscribe(setState), []);

  useEffect(() => {
    // Mirror horizontally when switching sides
    setIsMirrored(state.side === 'right');
  }, [state.side]);

  useEffect(() => {
    actionRef.current = state.action;
    if (state.action !== 'idle') {
      // Return to idle after animation cycle
      const t = setTimeout(() => {
        // Only reset if action unchanged
        if (actionRef.current === state.action) {
          characterController.set({ action: 'idle' });
        }
      }, 1800);
      return () => clearTimeout(t);
    }
  }, [state.action]);

  const containerClasses = useMemo(() => {
    const sideClasses = state.side === 'left' ? 'left-0 -translate-x-6' : 'right-0 translate-x-6';
    return `pointer-events-none absolute bottom-3 sm:bottom-0 z-20 ${sideClasses}`;
  }, [state.side]);

  const intensityScale = state.intensity === 'high' ? 1.2 : state.intensity === 'low' ? 0.9 : 1;

  const actionClass = (() => {
    switch (state.action) {
      case 'enter':
        return 'smom-enter';
      case 'wink':
        return 'smom-wink';
      case 'blow-kiss':
        return 'smom-kiss';
      case 'shimmy':
        return 'smom-shimmy';
      case 'dance':
        return 'smom-dance';
      case 'bounce':
        return 'smom-bounce';
      case 'point-left':
        return 'smom-point-left';
      case 'point-right':
        return 'smom-point-right';
      case 'idle':
      default:
        return 'smom-idle';
    }
  })();

  return (
    <div className={containerClasses} style={{ width: size, height: size }}>
      {/* Character body (stylized silhouette) */}
      <div
        className={`relative w-full h-full select-none ${actionClass}`}
        style={{
          transform: `scale(${intensityScale}) ${isMirrored ? 'scaleX(-1)' : ''}`,
          transformOrigin: 'bottom',
        }}
      >
        {/* Hair */}
        <div className="absolute top-[6%] left-[20%] w-[60%] h-[28%] rounded-b-[50%] bg-gradient-to-br from-pink-400 via-fuchsia-500 to-rose-500 blur-[0.5px] opacity-90" />
        {/* Head */}
        <div className="absolute top-[14%] left-[32%] w-[36%] h-[28%] bg-rose-200 rounded-full shadow-inner" />
        {/* Eye wink */}
        <div className="absolute top-[25%] left-[42%] w-[8%] h-[4%] bg-gray-800 rounded-full smom-eye" />
        {/* Lips */}
        <div className="absolute top-[38%] left-[42%] w-[16%] h-[8%] bg-rose-400 rounded-full smom-lips" />
        {/* Torso */}
        <div className="absolute top-[38%] left-[28%] w-[44%] h-[36%] bg-rose-300 rounded-[40%] smom-breathe shadow" />
        {/* Dress */}
        <div className="absolute top-[58%] left-[20%] w-[60%] h-[40%] bg-gradient-to-t from-rose-500 to-rose-400 rounded-t-[40%] smom-sway shadow-lg" />
        {/* Leg Left */}
        <div className="absolute top-[86%] left-[36%] w-[8%] h-[22%] bg-rose-300 rounded-full" />
        {/* Leg Right */}
        <div className="absolute top-[86%] left-[54%] w-[8%] h-[22%] bg-rose-300 rounded-full" />
        {/* Heels */}
        <div className="absolute top-[106%] left-[34%] w-[12%] h-[6%] bg-rose-700 rounded-[40%] rotate-[8deg]" />
        <div className="absolute top-[106%] left-[54%] w-[12%] h-[6%] bg-rose-700 rounded-[40%] -rotate-[6deg]" />
        {/* Sparkles */}
        <div className="absolute -top-2 left-2 w-2 h-2 bg-pink-300 rounded-full animate-ping" />
        <div className="absolute -top-1 right-4 w-1.5 h-1.5 bg-fuchsia-300 rounded-full animate-ping" />
      </div>
    </div>
  );
};

export default StevesMomCharacter;

