import { ComponentType } from '@angular/cdk/portal';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import * as _ from 'lodash';

import { CephfsModalComponent } from '~/app/core/modals/cephfs/cephfs-modal.component';
import { NfsModalComponent } from '~/app/core/modals/nfs/nfs-modal.component';

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  constructor(private dialog: MatDialog) {}

  openCephfs(onClose: (result: any) => void): void {
    this.open(CephfsModalComponent, onClose);
  }

  openNfs(onClose: (result: any) => void): void {
    this.open(NfsModalComponent, onClose);
  }

  open(component: ComponentType<any>, onClose?: (result: any) => void, config?: MatDialogConfig) {
    const ref = this.dialog.open(component, _.defaultsDeep(config, { width: '60%' }));
    ref.afterClosed().subscribe({
      next: (result) => {
        if (_.isFunction(onClose)) {
          onClose(result);
        }
      }
    });
  }
}
