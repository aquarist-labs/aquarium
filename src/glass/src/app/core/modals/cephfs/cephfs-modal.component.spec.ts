import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { CoreModule } from '~/app/core/core.module';
import { CephfsModalComponent } from '~/app/core/modals/cephfs/cephfs-modal.component';

describe('CephfsModalComponent', () => {
  let component: CephfsModalComponent;
  let fixture: ComponentFixture<CephfsModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        NoopAnimationsModule,
        CoreModule,
        TranslateModule.forRoot()
      ],
      providers: [
        {
          provide: MatDialogRef,
          useValue: {}
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CephfsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
