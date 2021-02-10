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

import { Status, StatusService } from '~/app/shared/services/api/status.service';

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
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const res: Status = { deployment_state: 'none' };
        return of(res);
      }),
      map((res: Status) => {
        let url: string;
        let result: boolean | UrlTree;
        switch (res.deployment_state) {
          case 'bootstrapping':
            url = '/installer/create/bootstrap';
            if (url === state.url) {
              result = true;
            } else {
              result = this.router.parseUrl(url);
            }
            break;
          case 'bootstrapped':
            url = '/installer/create/deployment';
            if (url === state.url) {
              result = true;
            } else {
              result = this.router.parseUrl(url);
            }
            break;
          case 'ready':
            result = this.router.parseUrl('/dashboard');
            break;
          case 'none':
          default:
            if (
              [
                '/installer/welcome',
                '/installer/install-mode',
                '/installer/create/bootstrap'
              ].includes(state.url)
            ) {
              result = true;
            } else {
              result = this.router.parseUrl('/installer');
            }
            break;
        }
        return result;
      })
    );
  }

  canActivateChild(
    childRoute: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    return this.canActivate(childRoute, state);
  }
}
