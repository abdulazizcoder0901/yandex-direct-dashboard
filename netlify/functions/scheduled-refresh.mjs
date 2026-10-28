// Har 15 daqiqada Yandex'dan yangi ma'lumot so'raladi (GitHub'ning o'z jadvali soatlab kechikadi)
import { dispatch } from '../lib/dispatch.mjs';

export default async () => {
  const res = await dispatch('jadval');
  console.log('Ma\'lumotni yangilash:', JSON.stringify(res));
};

export const config = { schedule: '*/15 * * * *' };
