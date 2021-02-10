import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import * as _ from 'lodash';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { NotificationService } from '~/app/shared/services/notification.service';

@Injectable({
  providedIn: 'root'
})
export class HttpErrorInterceptorService implements HttpInterceptor {
  constructor(private notificationService: NotificationService) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
      catchError((err) => {
        if (err instanceof HttpErrorResponse) {
          const notificationId: number = this.notificationService.show(err.message, {
            type: 'error'
          });

          /**
           * Decorate preventDefault method. If called, it will prevent a
           * notification to be shown.
           */
          _.set(err, 'preventDefault', () => {
            this.notificationService.cancel(notificationId);
          });
        }
        return throwError(err);
      })
    );
  }
}
