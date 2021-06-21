import { ComponentType } from '@angular/cdk/portal';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import * as _ from 'lodash';

import { FileServiceModalComponent } from '~/app/core/modals/file-service/file-service-modal.component';

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  constructor(private dialog: MatDialog) {}

  openFileService(onClose: (result: any) => void, type?: string): void {
    let config;
    if (type) {
      config = new MatDialogConfig();
      config.data = { type };
    }
    this.open(FileServiceModalComponent, onClose, config);
  }

  open(component: ComponentType<any>, onClose?: (result: any) => void, config?: MatDialogConfig) {
    config = _.defaultTo(config, {});
    _.defaultsDeep(config, { width: '60%' });
    const ref = this.dialog.open(component, config);
    ref.afterClosed().subscribe({
      next: (result) => {
        if (_.isFunction(onClose)) {
          onClose(result);
        }
      }
    });
  }
}
