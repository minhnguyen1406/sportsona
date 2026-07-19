// Universal load: runs on the server for first paint (so link previews /
// crawlers see real OG meta) and on the client for SPA navigations.
import { error } from '@sveltejs/kit';
import { PUBLIC_API_BASE_URL } from '$env/static/public';
import type { AskAnswerResponse } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
  const response = await fetch(`${PUBLIC_API_BASE_URL}/api/v1/ask/answers/${params.slug}`);
  if (!response.ok) {
    throw error(response.status === 404 ? 404 : 502, 'Answer not found');
  }
  const answer = (await response.json()) as AskAnswerResponse;
  return { answer };
};
