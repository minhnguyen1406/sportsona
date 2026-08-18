/** Race comment threads — a tree of comments (each with nested replies). */

import { apiFetch } from './client';

export interface CommentNode {
  id: number;
  user_id: number;
  author: string;
  body: string;
  is_deleted: boolean;
  created_at: string;
  replies: CommentNode[];
}

export const commentsApi = {
  /** The race's comment forest (roots with nested replies). Public. */
  list(raceId: number): Promise<CommentNode[]> {
    return apiFetch(`/api/v1/races/${raceId}/comments`);
  },
  /** Add a comment (parentId set → a reply). Auth required. */
  add(raceId: number, body: string, parentId?: number | null): Promise<CommentNode> {
    return apiFetch(`/api/v1/races/${raceId}/comments`, {
      method: 'POST',
      json: { body, parent_id: parentId ?? null }
    });
  },
  /** Tombstone your own comment. Auth required. */
  remove(commentId: number): Promise<void> {
    return apiFetch(`/api/v1/comments/${commentId}`, { method: 'DELETE' });
  }
};
