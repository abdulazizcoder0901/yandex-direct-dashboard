// "↻ Yangilash" tugmasi: POST /api/refresh
import { dispatch } from '../lib/dispatch.mjs';

export default async (req) => {
  if (req.method !== 'POST') return new Response('POST kerak', { status: 405 });
  const res = await dispatch('tugma');
  return Response.json(res, { status: res.ok ? 200 : 503, headers: { 'Cache-Control': 'no-store' } });
};

export const config = { path: '/api/refresh' };
