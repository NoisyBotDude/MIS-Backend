from fileinput import filename
from urllib.request import Request
from api.drivers import student

from api.drivers.student import student_drivers
from api.repository import admin_repo
from api.middlewares import authentication_middleware
from api.schemas.admin.admin_request_schema import admin_request_schemas
from api.schemas.student.request_schemas import student_request_schemas
from api.schemas.student.response_schemas import student_response_schemas
from api.utils.exceptions import exceptions
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from api.repository import admin_repo
from api.utils.save_student_data import save_data

from starlette.responses import FileResponse

import json


def construct_router():

    admin = APIRouter(tags=["Admin"])

    @admin.post("/notify/student")
    async def notify_by_batch():
        pass

    @admin.post("/add/student/subscription")
    async def add_student_subscription(
        request: admin_request_schemas.ManipulateStudentSubscriptionSchema,
    ):
        try:
            response = await student_drivers.Student().update_array_of_str(
                request.__dict__
            )
            return JSONResponse(status_code=200, content={"message": "info updated"})

        except exceptions.DuplicateStudent:
            return JSONResponse(
                status_code=409, content={"message": "info cannot be updated"}
            )

        except exceptions.UnexpectedError:
            return JSONResponse(
                status_code=500, content={"message": "internal server error"}
            )

    @admin.post("/remove/student/subscription")
    async def remove_student_subscription(
        request: admin_request_schemas.ManipulateStudentSubscriptionSchema,
    ):
        try:
            response = await student_drivers.Student().delete_from_array_of_str(
                request.__dict__
            )
            if response:
                return JSONResponse(
                    status_code=200,
                    content={"message": "subscription deleted successfully"},
                )

            return JSONResponse(
                status_code=500, content={"message": "subscription deletion failed"}
            )

        except exceptions.DuplicateStudent:
            return JSONResponse(
                status_code=409, content={"message": "info cannot be updated"}
            )

        except exceptions.UnexpectedError:
            return JSONResponse(
                status_code=500, content={"message": "internal server error"}
            )

    @admin.post("/verify/student")
    async def verify_student(request: Request):
        request = await request.json()

        response = await admin_repo.assign_otp(request["student_ids"])

        if response:
            return JSONResponse(
                status_code=200, content={"message": "otp assigned successfully"}
            )

        return JSONResponse(
            status_code=500,
            content={
                "message": """otp cannot be assigned successfully for all student"""
            },
        )

    @admin.get("/ban/student/{student_id}")
    async def ban_student_account(
        student_id: str,
        authorization = Depends(authentication_middleware.is_authenticated)
        ):
        response = await admin_repo.ban_student(student_id, authorization)

        if response == "already_banned":
            return JSONResponse(
                status_code=404, content={"message": "student aleady banned"}
            )

        elif response:
            return JSONResponse(
                status_code=200, content={"message": "student banned successfully"}
            )

        return JSONResponse(
            status_code=500, content={"message": "internal server error"}
        )

    @admin.delete("/delete/student/{student_id}")
    async def delete_student_account(
        student_id: str,
        authorization = Depends(authentication_middleware.is_authenticated)
        ):
        response = await admin_repo.delete_student(student_id, authorization)

        if response:
            return JSONResponse(
                status_code=200, content={"message": "student deleted successfully"}
            )

        return JSONResponse(
            status_code=404, content={"message": "student does not exist"}
        )

    @admin.get("/all_student")
    async def get_student_profile():
        try:
            response = await (
                student_drivers.Student().get_all_students()
            )

            return JSONResponse(
                status_code=200, 
                content=response
            )
        
        except Exception as e:
            print(e, "exception")

    @admin.post("/student/data")
    async def get_student_data():
        students = await (
            student_drivers.Student().get_all_students_data()
        )

        # print(students)
        save_data(students)
        
        if students:
            return JSONResponse(
                status_code=200,
                content= {
                    "message" : "training details saved succesfully"
                }
            )
        
        return JSONResponse(
            status_code=500,
            content= {
                "message" : "training details cannot be saved"
            }
        )

    @admin.get("/student/data")
    async def get_student_data(request: Request):
        filename = "student_data.xls"
        #send excel file
        return  FileResponse(
            filename,
            filename="student_data.xls",
            status_code=200,
            media_type="application/vnd.ms-excel"
        )

    return admin
