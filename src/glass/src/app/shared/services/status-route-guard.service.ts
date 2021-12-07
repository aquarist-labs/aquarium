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
  RouterStateSnapshot,
  UrlTree
} from '@angular/router';
import * as _ from 'lodash';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import {
  DeploymentErrorEnum,
  DeploymentState,
  DeploymentStateEnum,
  DeployService,
  DeployStatusReply,
  InitStateEnum
} from '~/app/shared/services/api/deploy.service';

@Injectable({
  providedIn: 'root'
})
export class StatusRouteGuardService implements CanActivate, CanActivateChild {
  constructor(private router: Router, private deployService: DeployService) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.deployService.status().pipe(
      catchError((err) => {
        // Do not show an error notification.
        if (_.isFunction(err.preventDefault)) {
          err.preventDefault();
        }
        const res: DeployStatusReply = {
          installed: false,
          status: {
            state: {
              init: InitStateEnum.none,
              deployment: DeploymentStateEnum.error
            },
            error: {
              code: DeploymentErrorEnum.unknownError
            }
          }
        };
        return of(res);
      }),
      map((res: DeployStatusReply): boolean | UrlTree => {
        const url = this.isUrlChangeNeeded(res.status.state, state.url);
        return _.isString(url) ? this.router.parseUrl(url) : true;
      })
    );
  }

  canActivateChild(
    childRoute: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.canActivate(childRoute, state);
  }

  private isUrlChangeNeeded(state: DeploymentState, currentUrl: string): string | boolean {
    const stageAndUrl = (
      initState: InitStateEnum,
      deploymentState: DeploymentStateEnum,
      urls: string[]
    ): string | boolean => {
      const redirectUrl = urls[0];
      return (
        state.init === initState &&
        state.deployment === deploymentState &&
        !urls.includes(currentUrl) &&
        !currentUrl.startsWith(redirectUrl) &&
        redirectUrl
      );
    };
    return (
      stageAndUrl(InitStateEnum.none, DeploymentStateEnum.none, [
        '/installer/welcome',
        '/installer/bootstrap'
      ]) ||
      stageAndUrl(InitStateEnum.none, DeploymentStateEnum.installing, ['/installer/bootstrap']) ||
      stageAndUrl(InitStateEnum.installed, DeploymentStateEnum.none, [
        '/installer/install-mode',
        '/installer/create',
        '/installer/join'
      ]) ||
      stageAndUrl(InitStateEnum.installed, DeploymentStateEnum.deploying, [
        '/installer/create',
        '/installer/join'
      ]) ||
      stageAndUrl(InitStateEnum.deployed, DeploymentStateEnum.deployed, [
        '/dashboard',
        '/hosts',
        '/services'
      ])
    );
  }
}
