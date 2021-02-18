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
   * @param config The notification configuration, including:
   *   type - 'info' or 'error'. Defaults to 'info'.
   *   duration - Defaults to 2000 milliseconds.
   * @returns The timeout ID that is set to be able to cancel the
   *   notification.
   */
  show(message: string, config?: NotificationConfig): number {
    config = _.defaultsDeep(config || {}, { type: NotificationType.info, duration: 2000 });
    return window.setTimeout(() => {
      this.snackBar.open(message, undefined, {
        duration: config!.duration,
        panelClass:
          config!.type === NotificationType.error ? 'glass-color-theme-error' : 'glass-theme-accent'
      });
    }, 5);
  }

  /**
   * Cancel a notification.
   *
   * @param id A number representing the ID of the timeout to be
   *   canceled.
   */
  cancel(id: number): void {
    window.clearTimeout(id);
  }
}
