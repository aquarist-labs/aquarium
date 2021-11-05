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
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { EMPTY, forkJoin, interval } from 'rxjs';
import { catchError, finalize, switchMap } from 'rxjs/operators';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { translate } from '~/app/i18n.helper';
import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DialogComponent } from '~/app/shared/components/dialog/dialog.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';
import { NodesService, TokenReply } from '~/app/shared/services/api/nodes.service';
import { Host, OrchService } from '~/app/shared/services/api/orch.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-hosts-page',
  templateUrl: './hosts-page.component.html',
  styleUrls: ['./hosts-page.component.scss']
})
export class HostsPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  pageStatus: PageStatus = PageStatus.none;
  data: Host[] = [];
  columns: DatatableColumn[];

  private firstLoadComplete = false;
  private rebooting = false;
  private inventory?: Inventory;

  constructor(
    private dialogService: DialogService,
    private localNodeService: LocalNodeService,
    private nodesService: NodesService,
    private orchService: OrchService,
    private router: Router
  ) {
    this.columns = [
      {
        name: TEXT('Hostname'),
        prop: 'hostname'
      },
      {
        name: TEXT('Address'),
        prop: 'address'
      },
      {
        name: '',
        prop: '',
        cellTemplateName: DatatableCellTemplateName.actionMenu,
        cellTemplateConfig: this.getActionMenu.bind(this)
      }
    ];
  }

  loadData(): void {
    if (this.rebooting) {
      // Skip loading the page content while the system is rebooting
      // to prevent error notifications.
      return;
    }
    if (!this.firstLoadComplete) {
      this.pageStatus = PageStatus.loading;
    }
    forkJoin({
      inventory: this.localNodeService.inventory(),
      hosts: this.orchService.hosts()
    })
      .pipe(
        finalize(() => {
          this.firstLoadComplete = true;
        })
      )
      .subscribe(
        (res: { inventory: Inventory; hosts: Host[] }) => {
          this.data = res.hosts;
          this.inventory = res.inventory;
          this.pageStatus = PageStatus.ready;
        },
        () => (this.pageStatus = PageStatus.loadingError)
      );
  }

  onShowToken(): void {
    this.nodesService.token().subscribe((res: TokenReply) => {
      this.dialogService.open(DeclarativeFormModalComponent, undefined, {
        title: TEXT('Authentication Token'),
        subtitle: TEXT('Use this token to authenticate a new node when adding it to the cluster.'),
        formConfig: {
          fields: [
            {
              type: 'text',
              name: 'token',
              value: res.token,
              readonly: true,
              hasCopyToClipboardButton: true,
              class: 'glass-text-monospaced'
            }
          ]
        },
        submitButtonVisible: false,
        cancelButtonText: TEXT('Close')
      });
    });
  }

  private getActionMenu(host: Host): DatatableActionItem[] {
    const items: DatatableActionItem[] = [];
    if (host.hostname === this.inventory?.hostname) {
      items.push(
        {
          type: 'menu',
          title: TEXT('Reboot'),
          callback: () => {
            this.dialogService.open(
              DialogComponent,
              (res: boolean) => {
                if (res) {
                  this.localNodeService.reboot().subscribe(() => {
                    this.rebooting = true;
                    this.blockUI.start(translate(TEXT('Please wait, rebooting the system ...')));
                    // Poll the given API endpoint until it succeeds again.
                    // If the authentication token is invalid, then the user
                    // will be redirected to the login page automatically.
                    const subscription = interval(5000)
                      .pipe(
                        switchMap(() =>
                          this.localNodeService.status().pipe(
                            catchError((error) => {
                              // Do not show an error notification.
                              if (_.isFunction(error.preventDefault)) {
                                error.preventDefault();
                              }
                              // The system is also up when the authentication
                              // fails. In that case the user is automatically
                              // redirected to the login page, but we should
                              // take care to cleanup correctly.
                              if (error.status === 401) {
                                subscription.unsubscribe();
                                this.blockUI.stop();
                                this.rebooting = false;
                              }
                              return EMPTY;
                            })
                          )
                        )
                      )
                      .subscribe(() => {
                        // Stop testing whether the system can be reached
                        // again; the system is up again.
                        subscription.unsubscribe();
                        // Unblock UI and continue fetching displayed data.
                        this.blockUI.stop();
                        this.rebooting = false;
                      });
                  });
                }
              },
              {
                type: 'yesNo',
                icon: 'danger',
                message: TEXT('Do you really want to reboot the system?')
              }
            );
          }
        },
        {
          type: 'menu',
          title: TEXT('Shutdown'),
          callback: () => {
            this.dialogService.open(
              DialogComponent,
              (res: boolean) => {
                if (res) {
                  this.localNodeService.shutdown().subscribe(() => {
                    this.router.navigate(['/shutdown']);
                  });
                }
              },
              {
                type: 'yesNo',
                icon: 'danger',
                message: TEXT('Do you really want to shutdown the system?')
              }
            );
          }
        }
      );
    }
    return items;
  }
}
