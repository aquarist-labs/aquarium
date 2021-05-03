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
  LocalNodeService,
  NodeStatus,
  StatusStageEnum
} from '~/app/shared/services/api/local.service';

@Injectable({
  providedIn: 'root'
})
export class StatusRouteGuardService implements CanActivate, CanActivateChild {
  constructor(private router: Router, private localNodeService: LocalNodeService) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.localNodeService.status().pipe(
      catchError((err) => {
        // Do not show an error notification.
        if (_.isFunction(err.preventDefault)) {
          err.preventDefault();
        }
        const res: NodeStatus = {
          /* eslint-disable @typescript-eslint/naming-convention */
          inited: false,
          node_stage: StatusStageEnum.unknown
        };
        return of(res);
      }),
      map((res: NodeStatus): boolean | UrlTree => {
        const url = this.isUrlChangeNeeded(res.node_stage, state.url);
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

  private isUrlChangeNeeded(stage: StatusStageEnum, currentUrl: string): string | boolean {
    const stageAndUrl = (isStage: StatusStageEnum, urls: string[]): string | boolean => {
      const redirectUrl = urls[0];
      return (
        stage === isStage &&
        !urls.includes(currentUrl) &&
        !currentUrl.startsWith(redirectUrl) &&
        redirectUrl
      );
    };
    return (
      stageAndUrl(StatusStageEnum.none, ['/installer']) ||
      stageAndUrl(StatusStageEnum.bootstrapping, ['/installer/create/wizard']) ||
      stageAndUrl(StatusStageEnum.bootstrapped, ['/installer/create/wizard', '/dashboard']) ||
      stageAndUrl(StatusStageEnum.joining, ['/installer/join/register']) ||
      stageAndUrl(StatusStageEnum.ready, ['/dashboard', '/hosts', '/services'])
    );
  }
}
