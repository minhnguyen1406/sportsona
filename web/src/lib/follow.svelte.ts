/**
 * Follow-state cache.
 *
 * Keeps lightweight in-memory sets of followed driver/constructor IDs so list
 * pages can show "Following" buttons without a per-row API call. Hydrated
 * once from /api/v1/users/me/followed-* and updated optimistically on
 * follow/unfollow actions.
 */

import { ApiError, usersApi } from '$lib/api';

class FollowStore {
  drivers = $state(new Set<string>());
  constructors = $state(new Set<string>());
  hydrated = $state(false);

  async hydrate() {
    if (this.hydrated) return;
    try {
      const [drivers, constructors] = await Promise.all([
        usersApi.listFollowedDrivers(),
        usersApi.listFollowedConstructors()
      ]);
      this.drivers = new Set(drivers.map((d) => d.driver_id));
      this.constructors = new Set(constructors.map((c) => c.constructor_id));
      this.hydrated = true;
    } catch (err) {
      // 401 is expected when logged out — silently leave sets empty
      if (!(err instanceof ApiError && err.status === 401)) {
        throw err;
      }
    }
  }

  isFollowingDriver(id: string) {
    return this.drivers.has(id);
  }

  isFollowingConstructor(id: string) {
    return this.constructors.has(id);
  }

  async toggleDriver(id: string) {
    const was = this.drivers.has(id);
    // Optimistic update
    if (was) this.drivers.delete(id);
    else this.drivers.add(id);
    this.drivers = new Set(this.drivers);
    try {
      if (was) await usersApi.unfollowDriver(id);
      else await usersApi.followDriver(id);
    } catch (err) {
      // Roll back on failure
      if (was) this.drivers.add(id);
      else this.drivers.delete(id);
      this.drivers = new Set(this.drivers);
      throw err;
    }
  }

  async toggleConstructor(id: string) {
    const was = this.constructors.has(id);
    if (was) this.constructors.delete(id);
    else this.constructors.add(id);
    this.constructors = new Set(this.constructors);
    try {
      if (was) await usersApi.unfollowConstructor(id);
      else await usersApi.followConstructor(id);
    } catch (err) {
      if (was) this.constructors.add(id);
      else this.constructors.delete(id);
      this.constructors = new Set(this.constructors);
      throw err;
    }
  }

  reset() {
    this.drivers = new Set();
    this.constructors = new Set();
    this.hydrated = false;
  }
}

export const follows = new FollowStore();
