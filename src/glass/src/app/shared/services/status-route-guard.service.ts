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

import { Status, StatusService, StatusStageEnum } from '~/app/shared/services/api/status.service';

@Injectable({
  providedIn: 'root'
})
export class StatusRouteGuardService implements CanActivate, CanActivateChild {
  constructor(private router: Router, private statusService: StatusService) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.statusService.status().pipe(
      catchError((err) => {
        // Do not show an error notification.
        if (_.isFunction(err.preventDefault)) {
          err.preventDefault();
        }
        const res: Status = {
          /* eslint-disable @typescript-eslint/naming-convention */
          node_stage: StatusStageEnum.unknown
        };
        return of(res);
      }),
      map((res: Status): boolean | UrlTree => {
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
      stageAndUrl(StatusStageEnum.bootstrapping, ['/installer/create/bootstrap']) ||
      stageAndUrl(StatusStageEnum.bootstrapped, ['/installer/create/deployment', '/dashboard']) ||
      stageAndUrl(StatusStageEnum.joining, ['/installer/join/register']) ||
      stageAndUrl(StatusStageEnum.ready, ['/dashboard'])
    );
  }
}
