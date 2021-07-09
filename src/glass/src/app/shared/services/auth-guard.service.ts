/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  CanActivateChild,
  Router,
  RouterStateSnapshot
} from '@angular/router';

import { AuthStorageService } from '~/app/shared/services/auth-storage.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuardService implements CanActivate, CanActivateChild {
  constructor(private authStorageService: AuthStorageService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    if (this.authStorageService.isLoggedIn()) {
      return true;
    }
    this.router.navigate(
      ['/login'],
      state.url === '/' ? undefined : { queryParams: { returnUrl: state.url } }
    );
    return false;
  }

  canActivateChild(childRoute: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    return this.canActivate(childRoute, state);
  }
}
