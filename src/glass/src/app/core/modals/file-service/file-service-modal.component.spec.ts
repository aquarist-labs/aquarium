import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatSliderChange } from '@angular/material/slider';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { ToastrModule } from 'ngx-toastr';

import { CoreModule } from '~/app/core/core.module';
import { FileServiceModalComponent } from '~/app/core/modals/file-service/file-service-modal.component';

describe('FileServiceModalComponent', () => {
  let component: FileServiceModalComponent;
  let fixture: ComponentFixture<FileServiceModalComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        NoopAnimationsModule,
        CoreModule,
        ToastrModule.forRoot(),
        TranslateModule.forRoot()
      ],
      providers: [
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {}
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FileServiceModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set required space [1]', () => {
    expect(component.formGroup.value.requiredSpace).toBe(0);
    component.onChangeRequiredSpace({
      target: {
        // @ts-ignore
        value: '10 G'
      }
    });
    expect(component.formGroup.value.requiredSpace).toBe(10737418240);
  });

  it('should set required space [2]', () => {
    expect(component.formGroup.value.requiredSpace).toBe(0);
    component.onInputRequiredSpace({
      value: 10737418240
    } as MatSliderChange);
    expect(component.formGroup.value.replicas).toBe(2);
    expect(component.formGroup.value.requiredSpace).toBe(10737418240);
    expect(component.formGroup.value.rawRequiredSpace).toBe(21474836480);
  });
});
