import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { translate } from '~/app/i18n.helper';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { RedundancyLevelPipe } from '~/app/shared/pipes/redundancy-level.pipe';
import { CephFSAuthorization, CephfsService } from '~/app/shared/services/api/cephfs.service';
import { Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';
import { ServiceDesc, ServicesService } from '~/app/shared/services/api/services.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-services-page',
  templateUrl: './services-page.component.html',
  styleUrls: ['./services-page.component.scss']
})
export class ServicesPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  loading = false;
  firstLoadComplete = false;
  data: ServiceDesc[] = [];
  columns: DatatableColumn[];

  constructor(
    private service: ServicesService,
    private bytesToSizePipe: BytesToSizePipe,
    private redundancyLevelPipe: RedundancyLevelPipe,
    private cephfsService: CephfsService,
    private dialogService: DialogService,
    private localNodeService: LocalNodeService
  ) {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'name',
        sortable: true
      },
      {
        name: TEXT('Type'),
        prop: 'type',
        sortable: true,
        cellTemplateName: 'map',
        cellTemplateConfig: {
          cephfs: 'CephFS',
          nfs: 'NFS'
        }
      },
      {
        name: TEXT('Allocated Size'),
        prop: 'allocation',
        pipe: this.bytesToSizePipe,
        sortable: true
      },
      {
        name: TEXT('Raw Size'),
        prop: 'raw_size',
        pipe: this.bytesToSizePipe,
        sortable: true
      },
      {
        name: TEXT('Flavor'),
        prop: 'replicas',
        pipe: this.redundancyLevelPipe,
        sortable: true
      },
      {
        name: '',
        prop: '',
        cellTemplateName: 'actionMenu',
        cellTemplateConfig: this.onActionMenu.bind(this)
      }
    ];
  }

  onAddService(): void {
    this.dialogService.openFileService((res) => {
      if (res) {
        this.loadData();
      }
    });
  }

  loadData(): void {
    this.loading = true;
    this.service.list().subscribe((data) => {
      this.data = data;
      this.loading = this.firstLoadComplete = true;
    });
  }

  onActionMenu(serviceDesc: ServiceDesc): DatatableActionItem[] {
    const result: DatatableActionItem[] = [];
    switch (serviceDesc.type) {
      case 'cephfs':
        result.push(
          {
            title: TEXT('Show credentials'),
            callback: (data: DatatableData) => {
              this.cephfsService.authorization(data.name).subscribe((auth: CephFSAuthorization) => {
                this.dialogService.open(DeclarativeFormModalComponent, undefined, {
                  width: '40%',
                  data: {
                    title: 'Credentials',
                    fields: [
                      {
                        type: 'text',
                        name: 'entity',
                        label: TEXT('Entity'),
                        value: auth.entity,
                        readonly: true
                      },
                      {
                        type: 'password',
                        name: 'key',
                        label: TEXT('Key'),
                        value: auth.key,
                        readonly: true,
                        hasCopyToClipboardButton: true
                      }
                    ],
                    submitButtonVisible: false,
                    cancelButtonText: TEXT('Close')
                  }
                });
              });
            }
          },
          {
            title: TEXT('Show mount command'),
            callback: (data: DatatableData) => {
              forkJoin({
                auth: this.cephfsService.authorization(data.name),
                inventory: this.localNodeService.inventory()
              }).subscribe((res) => {
                const ipAddr = this.getIpAddrFromInventory(res.inventory);
                const secret = res.auth.key;
                const name = res.auth.entity.replace('client.', '');
                const cmdArgs: Array<string> = [
                  'mount',
                  '-t',
                  'ceph',
                  '-o',
                  `secret=${secret},name=${name}`,
                  `${ipAddr}:/`,
                  '<MOUNTPOINT>'
                ];
                this.showMountCmdDialog(cmdArgs);
              });
            }
          },
          {
            title: TEXT('Remove service'),
            callback: (data: DatatableData) => {
              this.removeService(data.name);
            }
          }
        );
        break;
      case 'nfs':
        result.push({
          title: TEXT('Show mount command'),
          callback: (data: DatatableData) => {
            forkJoin({
              auth: this.cephfsService.authorization(data.name),
              inventory: this.localNodeService.inventory()
            }).subscribe((res) => {
              const ipAddr = this.getIpAddrFromInventory(res.inventory);
              const cmdArgs: Array<string> = [
                'mount',
                '-t',
                'nfs',
                `${ipAddr}:/${data.name}`,
                '<MOUNTPOINT>'
              ];
              this.showMountCmdDialog(cmdArgs);
            });
          }
        });
    }
    return result;
  }

  /**
   * Helper method to get the IP address from the inventory. If not
   * found, `<IPADDR>` will be returned instead.
   *
   * @param inventory The node's inventory.
   * @private
   */
  private getIpAddrFromInventory(inventory: Inventory): string {
    const physicalIfs = _.values(_.filter(inventory.nics, ['iftype', 'physical']));
    let ipAddr = _.get(_.first(physicalIfs), 'ipv4_address', '<IPADDR>') as string;
    if (ipAddr.indexOf('/')) {
      ipAddr = ipAddr.slice(0, ipAddr.indexOf('/'));
    }
    return ipAddr;
  }

  private showMountCmdDialog(cmdArgs: Array<string>): void {
    this.dialogService.open(DeclarativeFormModalComponent, undefined, {
      width: '60%',
      data: {
        title: TEXT('Mount command'),
        subtitle: TEXT('Use the following command line to mount the file system.'),
        fields: [
          {
            type: 'text',
            name: 'cmdline',
            value: cmdArgs.join(' '),
            readonly: true,
            hasCopyToClipboardButton: true,
            class: 'glass-text-monospaced'
          }
        ],
        submitButtonVisible: false,
        cancelButtonText: TEXT('Close')
      }
    });
  }

  private removeService(serviceName: string): void {
    this.dialogService.open(
      DialogComponent,
      (res: boolean) => {
        if (res) {
          this.blockUI.start(translate(TEXT('Please wait, removing service ...')));
          this.service
            .delete(serviceName)
            .pipe(finalize(() => this.blockUI.stop()))
            .subscribe(() => {
              this.loadData();
            });
        }
      },
      {
        width: '40%',
        data: {
          type: 'yesNo',
          icon: 'question',
          message: TEXT(`Do you really want to remove the service <strong>${serviceName}</strong>?`)
        }
      }
    );
  }
}
