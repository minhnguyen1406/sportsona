/**
 * Barrel for the API layer. Existing imports (`import { f1Api } from '$lib/api'`)
 * keep working; new code can also import from the specific module
 * (`import { f1Api } from '$lib/api/f1'`).
 *
 * Structure mirrors the backend: `client` is the shared foundation, each other
 * file is one domain (a sport like `f1`, or a feature like `ask`/`recap`).
 * Adding a sport = a new file here + one line in this barrel.
 */

export * from './client';
export * from './auth';
export * from './f1';
export * from './users';
export * from './ask';
export * from './recap';
export * from './stat';
