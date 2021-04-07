import { ComponentType } from '@angular/cdk/portal';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';

import { CephfsModalComponent } from '~/app/core/modals/cephfs/cephfs-modal.component';
import { NfsModalComponent } from '~/app/core/modals/nfs/nfs-modal.component';

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  private defaultDialogSettings = { width: '60%' };

  constructor(private dialog: MatDialog) {}

  openCephfs(onClose: (result: boolean) => void): void {
    this.open(CephfsModalComponent, onClose);
  }

  openNfs(onClose: (result: boolean) => void): void {
    this.open(NfsModalComponent, onClose);
  }

  open(
    component: ComponentType<any>,
    onClose: (result: boolean) => void,
    config: MatDialogConfig = this.defaultDialogSettings
  ) {
    const ref = this.dialog.open(component, config);
    ref.afterClosed().subscribe({ next: onClose });
  }
}
