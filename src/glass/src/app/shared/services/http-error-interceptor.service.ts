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
import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import * as _ from 'lodash';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AuthStorageService } from '~/app/shared/services/auth-storage.service';
import { NotificationService } from '~/app/shared/services/notification.service';

@Injectable({
  providedIn: 'root'
})
export class HttpErrorInterceptorService implements HttpInterceptor {
  constructor(
    private authStorageService: AuthStorageService,
    private notificationService: NotificationService,
    private router: Router
  ) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
      catchError((err) => {
        if (err instanceof HttpErrorResponse) {
          switch (err.status) {
            case 401:
              this.authStorageService.revoke();
              this.router.navigate(['/login']);
              break;
            default:
              const message = _.get(err, 'error.detail', err.message);
              const notificationId: number = this.notificationService.show(message, {
                type: 'error'
              });
              // Decorate preventDefault method. If called, it will prevent a
              // notification to be shown.
              (err as any).preventDefault = () => {
                this.notificationService.cancel(notificationId);
              };
              break;
          }
        }
        return throwError(err);
      })
    );
  }
}
