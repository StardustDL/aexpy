#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from aexpy.models import ApiDescription
from aexpy.models.description import AttributeEntry, FunctionEntry, Parameter
from aexpy.models.difference import DiffEntry
from aexpy.models.typing import AnyType

from ..checkers import DiffConstraint, DiffConstraintCollection, diffcons, fortype
from .parameters import changeParameter

TypeConstraints = DiffConstraintCollection()


@TypeConstraints.cons
@fortype(AttributeEntry)
@diffcons
def ChangeAttributeType(
    a: AttributeEntry, b: AttributeEntry, old: "ApiDescription", new: "ApiDescription"
):
    if a.type is not None and b.type is not None and a.type.id != b.type.id:
        if isinstance(a.type.type, AnyType) and a.annotation == "":
            return []
        if isinstance(b.type.type, AnyType) and b.annotation == "":
            return []
        return [
            DiffEntry(
                message=f"Change attribute type ({a.id}): {a.type.id} => {b.type.id}",
                data={"oldtype": a.type.id, "newtype": b.type.id},
            )
        ]
    return []


@TypeConstraints.cons
@fortype(FunctionEntry)
@diffcons
def ChangeReturnType(
    a: FunctionEntry, b: FunctionEntry, old: "ApiDescription", new: "ApiDescription"
):
    if a.returnType is not None and b.returnType is not None and a.returnType.id != b.returnType.id:
        if isinstance(a.returnType.type, AnyType) and a.returnAnnotation == "":
            return []
        if isinstance(b.returnType.type, AnyType) and b.returnAnnotation == "":
            return []
        return [
            DiffEntry(
                message=f"Change return type ({a.id}): {a.returnType.id} => {b.returnType.id}",
                data={"oldtype": a.returnType.id, "newtype": b.returnType.id},
            )
        ]
    return []


@TypeConstraints.cons
@changeParameter
def ChangeParameterType(
    a: Parameter | None, b: Parameter | None, old: FunctionEntry, new: FunctionEntry
):
    if a is not None and b is not None:
        if a.name == b.name:
            if a.type is not None and b.type is not None and a.type.id != b.type.id:
                if isinstance(a.type.type, AnyType) and a.annotation == "":
                    return []
                if isinstance(b.type.type, AnyType) and b.annotation == "":
                    return []
                return [
                    DiffEntry(
                        message=f"Change parameter type ({old.id}): {a.name}: {a.type.id} => {b.type.id}",
                        data={"oldtype": a.type.id, "newtype": b.type.id},
                    )
                ]
    return []
