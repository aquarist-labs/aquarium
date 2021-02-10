import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import * as _ from 'lodash';

// eslint-disable-next-line no-shadow
export enum NotificationType {
  info = 'info',
  error = 'error'
}

export type NotificationConfig = {
  type?: 'info' | 'error';
  duration?: number;
};

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  constructor(private snackBar: MatSnackBar) {}

  /**
   * Show a notification.
   *
   * @param message The message to be displayed.
   * @param config The time the notification is displayed.
   *   Defaults to 2000 milliseconds.
   */
  show(message: string, config: NotificationConfig) {
    _.defaultsDeep(config, { type: NotificationType.info, duration: 2000 });
    this.snackBar.open(message, undefined, {
      duration: config.duration,
      panelClass: config.type === NotificationType.error ? 'glass-color-theme-error' : undefined
    });
  }
}
