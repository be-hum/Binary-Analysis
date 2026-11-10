# Ghidra MCP 도구 목록

- 출처: [bethington/ghidra-mcp](https://github.com/bethington/ghidra-mcp) **v7.0.0** 태그의 `tests/endpoints.json` (자동 생성)
- 대상 환경: Ghidra 12.1.4 / Java 21 (v7.0.0 빌드 기준)
- 총 **209개** — 조회(GET) 100개 / 변경 가능(POST) 109개
- 제공 서버: 둘 다 186개 · GUI만 19개 · headless만 4개
- MCP 도구 이름 = HTTP 경로에서 앞의 `/`를 빼고 `/`를 `_`로 바꾼 것 (예: `/debugger/status` → `debugger_status`)
- 모든 도구는 선택 인자 `program`(대상 프로그램 지정)을 받으며, 아래 인자 목록에서는 생략함

## 표기

| 표기 | 의미 |
|---|---|
| GET | 조회 (Ghidra DB를 변경하지 않음). 예외는 🔸 표시 |
| POST | 변경 가능 (이름/타입/주석 변경, 생성·삭제, 실행 등). 이름상 조회성인 것은 🔹 표시 |
| 🔸상태변경 | GET이지만 저장·활성 프로그램 전환 등 상태를 바꿈 — 에이전트 읽기 전용 세트에서 제외 권장 |
| 🔹조회성 | POST지만 이름/설명상 조회 목적 (실제 부작용은 소스로 확인 필요) |
| ⭐최소 | README의 최소 읽기 전용 세트 (자체 순환: 진입점→함수 목록→디컴파일/callees) |
| ➕다음 | README가 권장하는 다음 추가 도구 |
| ⚠️ | 삭제·실행·디버거 등 되돌리기 어렵거나 위험한 변경 도구 |

## 카테고리 요약

| 카테고리 | 도구 수 | GET | POST |
|---|---:|---:|---:|
| [프로그램·세션](#program) (`program`) | 33 | 15 | 18 |
| [목록 조회](#listing) (`listing`) | 12 | 12 | 0 |
| [함수](#function) (`function`) | 23 | 5 | 18 |
| [상호 참조(xref)](#xref) (`xref`) | 8 | 5 | 3 |
| [심볼](#symbol) (`symbol`) | 4 | 1 | 3 |
| [주석](#comment) (`comment`) | 4 | 1 | 3 |
| [데이터 타입](#datatype) (`datatype`) | 32 | 10 | 22 |
| [분석](#analysis) (`analysis`) | 20 | 14 | 6 |
| [문서화](#documentation) (`documentation`) | 11 | 8 | 3 |
| [악성코드 분석](#malware) (`malware`) | 5 | 5 | 0 |
| [에뮬레이션](#emulation) (`emulation`) | 2 | 0 | 2 |
| [디버거](#debugger) (`debugger`) | 16 | 10 | 6 |
| [프로젝트](#project) (`project`) | 11 | 2 | 9 |
| [Ghidra Server(공유)](#server) (`server`) | 18 | 7 | 11 |
| [Headless 전용](#headless) (`headless`) | 3 | 0 | 3 |
| [유틸리티](#utility) (`utility`) | 5 | 4 | 1 |
| [Getter](#getter) (`getter`) | 1 | 1 | 0 |
| [시스템](#system) (`system`) | 1 | 0 | 1 |

<a id="program"></a>
## 프로그램·세션 (`program`) — 33개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `analysis_status` | GET | 둘 다 |  | - | Get auto-analysis status for open programs |
| `get_address_spaces` | GET | 둘 다 |  | - | List all physical and overlay address spaces in the program (overlays include is_overlay flag and overlayed_space name) |
| `get_language_metadata` | GET | 둘 다 |  | `include_registers`, `include_default_symbols` | Dump the program's language description: address spaces, registers, default symbols, endianness, pointer size (issue #192). |
| `get_metadata` | GET | 둘 다 | ⭐최소 | - | Get program metadata |
| `get_program_options` | GET | 둘 다 |  | `group` | Read all options in a program option group with types, current values, defaults, and descriptions. |
| `get_property` | GET | 둘 다 |  | `map`, `address` | Read the value stored at an address in a property map. |
| `list_bookmarks` | GET | 둘 다 |  | `category`, `address` | List bookmarks |
| `list_open_programs` | GET | 둘 다 |  | - | List open programs |
| `list_project_files` | GET | 둘 다 |  | `folder` | List project files |
| `list_properties` | GET | 둘 다 |  | `map`, `start`, `end`, `offset`, `limit` | List (address, value) entries stored in a property map, with pagination. |
| `list_scripts` | GET | 둘 다 |  | `filter` | List available Ghidra scripts |
| `read_memory` | GET | 둘 다 |  | `address`, `length` | Read raw memory |
| `save_all_programs` | GET | 둘 다 | 🔸상태변경 | - | Save all open programs |
| `save_program` | GET | 둘 다 | 🔸상태변경 | - | Save current program |
| `switch_program` | GET | 둘 다 | 🔸상태변경 | - | Switch current program |
| `close_program` | POST | 둘 다 |  | `name`, `save` | Close an open program by project path or name. |
| `create_memory_block` | POST | 둘 다 |  | `name`, `address`, `size`, `read`, `write`, `execute`, `volatile`, `comment` 외 5개 | Create memory block, optionally initialized with byte contents (hex or base64) |
| `create_property_map` | POST | 둘 다 |  | `name`, `type` | Create a user property map to store typed values keyed by address. |
| `delete_bookmark` | POST | 둘 다 | ⚠️ | `address`, `category` | Delete bookmark |
| `delete_property_map` | POST | 둘 다 | ⚠️ | `name` | Delete a user property map and all values it holds. |
| `exit_ghidra` | POST | 둘 다 |  | - | Save and exit Ghidra |
| `import_file` | POST | 둘 다 | ⚠️ | `file_path`, `project_folder`, `language`, `compiler_spec`, `auto_analyze` | Import a binary file from disk into the current Ghidra project and open it. |
| `open_program` | POST | 둘 다 |  | `path`, `auto_analyze` | Open program from project |
| `reanalyze` | POST | 둘 다 |  | - | Trigger full auto-analysis on a program |
| `remove_program_option` | POST | 둘 다 |  | `group`, `name` | Remove an option from a program option group. |
| `remove_property` | POST | 둘 다 |  | `map`, `address` | Remove the value stored at a single address in a property map. |
| `run_ghidra_script` | POST | 둘 다 | ⚠️ | `script_name`, `args`, `timeout_seconds`, `capture_output` | Run script with output capture |
| `run_script_inline` | POST | 둘 다 | ⚠️ | `code`, `args` | Run inline script code |
| `set_bookmark` | POST | 둘 다 |  | `address`, `category`, `comment` | Set bookmark |
| `set_image_base` | POST | 둘 다 |  | `address` | Set the base address of the program (rebases all addresses) |
| `set_memory_block` | POST | 둘 다 |  | `block`, `address`, `read`, `write`, `execute`, `volatile` | Change an existing memory block's permissions or volatility. |
| `set_program_option` | POST | 둘 다 |  | `group`, `name`, `value`, `type` | Set a typed program option. |
| `set_property` | POST | 둘 다 |  | `map`, `address`, `value` | Set a value at an address in a property map. |

<a id="listing"></a>
## 목록 조회 (`listing`) — 12개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `convert_number` | GET | 둘 다 |  | `text`, `size` | Convert number between bases |
| `find_functions` | GET | 둘 다 | ⭐최소 | `name_pattern`, `pattern`, `query`, `name`, `regex`, `min_xrefs`, `max_xrefs`, `calling_convention` 외 7개 | Find functions: every filter is optional, so with none it lists the whole program a page at a time. |
| `get_entry_points` | GET | 둘 다 | ⭐최소 | - | Get program entry points |
| `get_external_location` | GET | 둘 다 |  | `address`, `dll_name` | Get external location details |
| `get_function_count` | GET | 둘 다 |  | - | Return the number of functions in the loaded program |
| `list_calling_conventions` | GET | 둘 다 |  | - | List available calling conventions |
| `list_data_items_by_xrefs` | GET | 둘 다 |  | `offset`, `limit`, `format`, `filter`, `type_filter`, `min_xrefs`, `include_all_sections` | List data sorted by xref count |
| `list_globals` | GET | 둘 다 |  | `offset`, `limit`, `filter`, `type_filter`, `min_xrefs`, `include_all_sections`, `name_substring` | List global variables |
| `list_program_items` | GET | 둘 다 | ➕다음 | `kind`, `offset`, `limit` | List one kind of program inventory with pagination. |
| `list_shadowed_globals` | GET | 둘 다 |  | `offset`, `limit`, `include_all_sections` | List named global DATA symbols that have NO type of their own because a larger data unit starting at an earlier address covers them. |
| `list_strings` | GET | 둘 다 | ➕다음 | `offset`, `limit`, `filter` | List defined strings |
| `search_strings` | GET | 둘 다 |  | `search_term`, `min_length`, `encoding`, `offset`, `limit` | Search defined strings by a regex/substring pattern |

<a id="function"></a>
## 함수 (`function`) — 23개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `disassemble_function` | GET | 둘 다 |  | `address` | Disassemble function |
| `force_decompile` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `variant` | Force fresh decompilation (output stamped with language_id + variant; optional variant= is checked against the loaded one) |
| `get_functions` | GET | 둘 다 | ⭐최소 | `function`, `address`, `name`, `function_address`, `function_name`, `functions`, `fields`, `include_call_context` 외 5개 | Everything about one or many functions in a single call. |
| `list_class_members` | GET | 둘 다 |  | `class_name`, `offset`, `limit` | List the member functions of a C++ class. |
| `list_function_tags` | GET | 둘 다 |  | `offset`, `limit` | List all program-wide function tag definitions with their use counts. |
| `add_function_tag` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `tags`, `tag_comments`, `assignments` | Attach tags to ONE function (function + tags) OR MANY in one transaction (assignments=[{function,tags}, ...]). |
| `batch_rename_function_components` | POST | 둘 다 |  | `function`, `address`, `function_address`, `function_name`, `parameter_renames`, `local_renames`, `return_type` | Batch rename function components |
| `clear_flow_and_repair` | POST | 둘 다 |  | `start_address`, `end_address` | Run Ghidra's GUI 'Clear Flow and Repair' action on a seed range: clears instruction flow reachable from the seed, then repairs function bodies and re-disasse... |
| `clear_instruction_flow_override` | POST | 둘 다 |  | `address` | Clear flow override |
| `create_function` | POST | 둘 다 |  | `address`, `name`, `disassemble_first` | Create function at address |
| `delete_function` | POST | 둘 다 | ⚠️ | `function`, `address`, `name`, `function_address`, `function_name` | Delete function at address |
| `delete_function_tag` | POST | 둘 다 | ⚠️ | `name` | Delete a program-wide function tag definition. |
| `disassemble_bytes` | POST | 둘 다 |  | `start_address`, `end_address`, `length`, `restrict_to_execute_memory`, `include_instructions`, `max_instructions` | Disassemble byte range |
| `remove_function_tag` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `tags`, `assignments` | Detach one or more tags from a function. |
| `rename_function` | POST | 둘 다 |  | `old_name`, `function_address`, `function`, `oldName`, `new_name`, `strict_mode` | Rename function by name |
| `rename_variables` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `variable_renames`, `force_individual` | Batch rename variables |
| `set_function_no_return` | POST | 둘 다 |  | `function_address`, `no_return`, `noReturn` | Set no-return attribute |
| `set_function_prototype` | POST | 둘 다 |  | `function_address`, `prototype`, `calling_convention` | Set function prototype (return type, param types, calling convention). |
| `set_function_tag_comment` | POST | 둘 다 |  | `name`, `comment` | Update the comment/description on an existing program-wide function tag. |
| `set_function_this_type` | POST | 둘 다 |  | `function_address`, `this_type`, `thisType` | Set the decompiler/database type of the implicit 'this' pointer (ECX on x86 __thiscall/__fastcall). |
| `set_variable_storage` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `variable_name`, `storage` | Set variable storage |
| `set_variable_type` | POST | 둘 다 |  | `function_address`, `variable_name`, `parameter_name`, `new_type` | Set the data type of a function variable (local OR parameter) by name at the decompiler (high-level) layer. |
| `set_variables` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `variables` | Set types and names for multiple variables atomically. |

<a id="xref"></a>
## 상호 참조(xref) (`xref`) — 8개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `analyze_call_graph` | GET | 둘 다 |  | `start_function`, `end_function`, `analysis_type` | Analyze function call graph patterns |
| `get_full_call_graph` | GET | 둘 다 |  | `format`, `limit` | Get full call graph |
| `get_function_call_graph` | GET | 둘 다 | ➕다음 | `function`, `name`, `address`, `function_name`, `function_address`, `depth`, `direction` | Get call graph |
| `get_xrefs_from` | GET | 둘 다 |  | `address`, `offset`, `limit` | Get references from address |
| `get_xrefs_to` | GET | 둘 다 | ➕다음 | `address`, `addresses`, `offset`, `limit` | Get references to address |
| `add_memory_reference` | POST | 둘 다 |  | `from_address`, `to_address`, `ref_type`, `source_type`, `operand_index` | Create a user-defined cross-reference between two memory addresses that the auto-analyzer can't infer (runtime-populated pointer tables, vtables, late-bound ... |
| `get_assembly_context` | POST | 둘 다 | 🔹조회성 | `xref_sources`, `context_instructions` | Get assembly context |
| `remove_reference` | POST | 둘 다 |  | `from_address`, `to_address`, `operand_index` | Remove memory cross-reference(s) from one address to another — the inverse of add_memory_reference. |

<a id="symbol"></a>
## 심볼 (`symbol`) — 4개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `can_rename_at_address` | GET | 둘 다 |  | `address` | Check if address can be renamed |
| `create_label` | POST | 둘 다 |  | `address`, `name`, `labels` | Create label |
| `delete_label` | POST | 둘 다 | ⚠️ | `address`, `name`, `labels` | Delete label at address |
| `rename_symbol` | POST | 둘 다 |  | `target`, `address`, `function_address`, `new_name`, `kind`, `old_name`, `strict_mode` | Rename a symbol of any kind. |

<a id="comment"></a>
## 주석 (`comment`) — 4개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `get_comment` | GET | 둘 다 |  | `address`, `addresses`, `only_with_comments` | Get listing comments (plate/pre/eol/post/repeatable) at ANY address, including data addresses (works on functions and data globals alike), for ONE address (a... |
| `batch_set_comments` | POST | 둘 다 |  | `address`, `decompiler_comments`, `disassembly_comments`, `plate_comment` | Set multiple comments |
| `clear_function_comments` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `clear_plate`, `clear_pre`, `clear_eol` | Clear all comments for a function |
| `set_comment` | POST | 둘 다 |  | `address`, `comment`, `type` | Set a listing comment of a given kind (plate/pre/eol/post/repeatable) at ANY address, including data addresses. |

<a id="datatype"></a>
## 데이터 타입 (`datatype`) — 32개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `analyze_global_completeness` | GET | 둘 다 |  | `address`, `compact` | Score a global variable's documentation completeness on a budgeted 0-100 scale — the data-address analog of analyze_function_completeness. |
| `audit_global` | GET | 둘 다 |  | `address` | Audit a global variable's documentation state. |
| `audit_globals_in_function` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name` | Audit every global variable referenced from within a function in one call. |
| `find_data_types` | GET | 둘 다 |  | `pattern`, `category`, `kind`, `categories`, `offset`, `limit` | Find data types by name or path pattern, category and kind, one record per type (name, kind, category, size, path). |
| `get_enum_values` | GET | 둘 다 |  | `enum_name` | Get enumeration values |
| `get_struct_layout` | GET | 둘 다 |  | `struct_name` | Get structure layout |
| `get_type_size` | GET | 둘 다 |  | `type_name` | Get data type size and info |
| `get_valid_data_types` | GET | 둘 다 |  | `category` | Get valid data type names |
| `validate_data_type` | GET | 둘 다 |  | `address`, `type_name` | Validate data type syntax |
| `validate_function_prototype` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `prototype`, `calling_convention` | Validate function prototype |
| `add_struct_field` | POST | 둘 다 |  | `struct_name`, `field_name`, `field_type`, `offset` | Add struct field |
| `analyze_struct_field_usage` | POST | 둘 다 |  | `address`, `struct_name`, `max_functions` | Analyze struct field usage |
| `apply_data_classification` | POST | 둘 다 |  | `address`, `classification`, `name`, `comment`, `type_definition` | Apply data classification |
| `apply_data_type` | POST | 둘 다 |  | `address`, `type_name`, `clear_existing`, `strict_mode` | Apply data type |
| `clone_data_type` | POST | 둘 다 |  | `source_type`, `new_name` | Clone data type |
| `create_data_type_category` | POST | 둘 다 |  | `category_path` | Create data type category |
| `create_derived_type` | POST | 둘 다 |  | `kind`, `base_type`, `name`, `length` | Create a type built on another: a typedef alias, an array or a pointer. |
| `create_enum` | POST | 둘 다 |  | `name`, `values`, `size` | Create enumeration |
| `create_function_signature` | POST | 둘 다 |  | `name`, `return_type`, `parameters` | Create function signature type |
| `create_struct` | POST | 둘 다 |  | `name`, `fields`, `replace_placeholder` | Create structure. |
| `create_union` | POST | 둘 다 |  | `name`, `fields` | Create union |
| `delete_data_type` | POST | 둘 다 | ⚠️ | `type_name`, `resolve_demangler_duplicate` | Delete data type |
| `import_data_types` | POST | 둘 다 | ⚠️ | `source`, `format` | Import data types from GDT |
| `modify_struct_field` | POST | 둘 다 |  | `struct_name`, `field_name`, `new_type`, `new_name` | Modify a field in a structure: retype it (new_type, which also embeds a struct by value, e.g. |
| `move_data_type_to_category` | POST | 둘 다 |  | `type_name`, `category_path` | Move data type to category |
| `recreate_struct` | POST | 둘 다 |  | `name`, `fields`, `size`, `replace_placeholder`, `force` | Replace a structure in one step: optionally remove an existing same-named type, then create with fields JSON (same shape as create_struct). |
| `remove_struct_field` | POST | 둘 다 |  | `struct_name`, `field_name` | Remove struct field |
| `rename_data_type` | POST | 둘 다 |  | `old_name`, `new_name` | Rename a data type (struct, union, enum, typedef) in place, preserving existing applications of it |
| `resize_struct` | POST | 둘 다 |  | `name`, `new_size`, `preserve_fields`, `force` | Grow or shrink an existing structure by total byte size. |
| `resolve_duplicate_type` | POST | 둘 다 |  | `type_name`, `delete_demangler_stub` | Find duplicate data types by simple name; delete unused /Demangler size-1 stubs when a larger canonical type exists. |
| `set_global` | POST | 둘 다 |  | `address`, `name`, `type_name`, `array_length`, `plate_comment`, `strict_mode`, `allow_evict` | Atomically apply name + type + plate-comment + array length to a global variable. |
| `suggest_field_names` | POST | 둘 다 |  | `struct_address`, `struct_size` | Suggest field names |

<a id="analysis"></a>
## 분석 (`analysis`) — 20개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `analyze_control_flow` | GET | 둘 다 |  | `function_name` | Analyze control flow |
| `analyze_dataflow` | GET | 둘 다 |  | `address`, `variable`, `direction`, `max_steps` | Trace value propagation through a function (PCode graph, forward/backward) |
| `analyze_for_documentation` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `variant` | Composite RE documentation analysis (decompile + classify + variables + completeness); decompiled_code is stamped with language_id + variant, and withheld if... |
| `analyze_function_complete` | GET | 둘 다 |  | `function`, `name`, `address`, `function_address`, `function_name`, `include_xrefs`, `include_callees`, `include_callers` 외 4개 | Comprehensive single-call function analysis. |
| `analyze_function_completeness` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `compact`, `addresses` | Analyze documentation completeness |
| `find_code_gaps` | GET | 둘 다 |  | `min_size`, `offset`, `limit` | Find gaps of undefined bytes between functions in executable memory |
| `find_dead_code` | GET | 둘 다 |  | `function_name` | Find dead code |
| `find_next_undefined_function` | GET | 둘 다 |  | `start_address`, `criteria`, `pattern`, `direction` | Find next undefined function |
| `find_similar_functions` | GET | 둘 다 |  | `target_function`, `threshold` | Find similar functions |
| `get_function_pcode` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `granularity` | Dump raw P-code for a function (issue #192). |
| `inspect_memory_content` | GET | 둘 다 |  | `address`, `length`, `detect_strings` | Inspect memory bytes |
| `list_analyzers` | GET | 둘 다 |  | - | List available analysis plugins |
| `search_byte_patterns` | GET | 둘 다 |  | `pattern`, `mask` | Search for byte patterns |
| `search_instructions` | GET | 둘 다 |  | `mnemonic`, `operand_pattern`, `function`, `limit` | Search for instructions by mnemonic and/or operand substring. |
| `analyze_data_region` | POST | 둘 다 |  | `address`, `max_scan_bytes`, `include_xref_map`, `include_boundary_detection` | Analyze data region |
| `apply_documentation` | POST | 둘 다 |  | `address`, `target_address`, `entries`, `goto`, `name`, `function_name`, `prototype`, `calling_convention` 외 11개 | Apply documentation to ONE function (fields at the top level) OR MANY (entries=[{address, ...}, ...]). |
| `configure_analyzer` | POST | 둘 다 |  | `name`, `enabled` | Configure an analysis plugin |
| `detect_array_bounds` | POST | 둘 다 |  | `address`, `max_scan_range` | Detect array bounds |
| `get_field_access_context` | POST | 둘 다 | 🔹조회성 | `struct_address`, `field_offset`, `num_examples` | Get field access context |
| `run_analysis` | POST | 둘 다 |  | - | Run auto-analysis on the current program |

<a id="documentation"></a>
## 문서화 (`documentation`) — 11개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `batch_string_anchor_report` | GET | 둘 다 |  | `pattern` | Report of source file strings and their FUN_* functions |
| `bulk_fuzzy_match` | GET | 둘 다 |  | `source_program`, `target_program`, `threshold`, `offset`, `limit`, `filter` | Bulk cross-binary function matching |
| `compare_programs_documentation` | GET | 둘 다 |  | - | Compare documentation across programs |
| `diff_functions` | GET | 둘 다 |  | `address_a`, `address_b`, `program_a`, `program_b` | Diff two functions |
| `find_similar_functions_fuzzy` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `source_program`, `target_program`, `threshold` 외 1개 | Cross-binary fuzzy function matching. |
| `find_undocumented_by_string` | GET | 둘 다 |  | `address` | Find undocumented functions referencing string |
| `get_function_documentation` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name` | Export function documentation |
| `get_function_hash` | GET | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `offset`, `limit`, `filter` | Compute the normalized opcode hash of ONE function (function=), or of MANY in one call by omitting it: every function, paged, optionally only the documented ... |
| `archive_ingest_function` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `version_override`, `dry_run` | Ingest a single function's documentation into the cross-version archive (the doc archive service configured via GHIDRA_MCP_ARCHIVE_URL). |
| `archive_ingest_program` | POST | 둘 다 |  | `version_override`, `limit`, `skip_default_named`, `dry_run` | Bulk-ingest every function in a program into the cross-version documentation archive. |
| `merge_program_documentation` | POST | 둘 다 |  | `source`, `target`, `dry_run` | Bulk merge: copy all RE documentation (function names, signatures, plate comments, instruction comments at EOL/PRE/POST, non-default labels & global symbols)... |

<a id="malware"></a>
## 악성코드 분석 (`malware`) — 5개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `analyze_api_call_chains` | GET | 둘 다 |  | - | Analyze API call chains |
| `detect_crypto_constants` | GET | 둘 다 |  | - | Detect crypto constants |
| `detect_malware_behaviors` | GET | 둘 다 |  | - | Detect malware behaviors |
| `extract_iocs_with_context` | GET | 둘 다 |  | - | Extract IOCs with context |
| `find_anti_analysis_techniques` | GET | 둘 다 |  | - | Find anti-analysis techniques |

<a id="emulation"></a>
## 에뮬레이션 (`emulation`) — 2개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `emulate_function` | POST | 둘 다 |  | `function`, `address`, `name`, `function_address`, `function_name`, `registers`, `memory`, `max_steps` 외 2개 | Emulate a single function with controlled register/memory inputs. |
| `emulate_hash_batch` | POST | 둘 다 |  | `hash_function_address`, `string_register`, `result_register`, `target_hash`, `candidates`, `initial_registers`, `wide_string` | Brute-force API hash resolution. |

<a id="debugger"></a>
## 디버거 (`debugger`) — 16개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `debugger_dynamic_to_static` | GET | GUI만 |  | `address` | Translate a runtime dynamic address from the current trace back to a static Ghidra program address |
| `debugger_launch_offers` | GET | GUI만 |  | - | List available debugger launch/attach options for the current program |
| `debugger_list_breakpoints` | GET | GUI만 |  | - | List all breakpoints in the current trace |
| `debugger_modules` | GET | GUI만 |  | - | List modules (DLLs/EXEs) loaded in the debugged process |
| `debugger_read_memory` | GET | GUI만 |  | `address`, `size` | Read memory from the debugged process. |
| `debugger_registers` | GET | GUI만 |  | - | Read CPU registers from the current debug trace snapshot. |
| `debugger_stack_trace` | GET | GUI만 |  | `depth` | Get the call stack backtrace for the current thread |
| `debugger_static_to_dynamic` | GET | GUI만 |  | `address` | Translate a static Ghidra program address to a runtime dynamic address in the current trace |
| `debugger_status` | GET | GUI만 |  | - | Get debugger status: active trace, thread, execution state, module count |
| `debugger_traces` | GET | GUI만 |  | - | List all open debug traces |
| `debugger_interrupt` | POST | GUI만 | ⚠️ | - | Interrupt (break into) the running target |
| `debugger_launch` | POST | GUI만 | ⚠️ | `executable_path`, `args`, `cwd`, `timeout_seconds`, `offer`, `python_executable`, `windbg_dir` | Launch an executable through Ghidra's Trace RMI debugger launcher |
| `debugger_remove_breakpoint` | POST | GUI만 | ⚠️ | `address` | Remove a breakpoint at an address |
| `debugger_resume` | POST | GUI만 | ⚠️ | - | Resume execution of the debugged process |
| `debugger_set_breakpoint` | POST | GUI만 | ⚠️ | `address` | Set a software execution breakpoint at an address in the trace |
| `debugger_step` | POST | GUI만 | ⚠️ | `kind` | Single-step the debugged process: into the next instruction (follows calls), over it (does not follow calls), or out of the current function (run to return). |

<a id="project"></a>
## 프로젝트 (`project`) — 11개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `get_project_info` | GET | 둘 다 |  | - | Get info about the currently open project |
| `list_projects` | GET | headless만 |  | `searchDir` | List available Ghidra projects |
| `archive_project` | POST | 둘 다 |  | `output_dir`, `output_name` | Archive the currently open project to a Ghidra-native .gar file. |
| `create_folder` | POST | 둘 다 |  | `path` | Create a folder in the project |
| `delete_file` | POST | 둘 다 | ⚠️ | `filePath` | Delete a file from the project |
| `delete_project` | POST | headless만 | ⚠️ | `projectPath` | Delete a Ghidra project |
| `export_program` | POST | 둘 다 |  | `program_name`, `output_dir`, `output_name` | Export an open or project-resident program to a Ghidra Zip File (.gzf). |
| `import_program` | POST | 둘 다 | ⚠️ | `gzf_path`, `target_folder`, `target_name`, `overwrite` | Import a Ghidra Zip File (.gzf) into the currently open project as a new DomainFile under target_folder (default '/'). |
| `move_file` | POST | 둘 다 |  | `filePath`, `destFolder` | Move a program file to a different folder in the project, preserving analysis and documentation. |
| `move_folder` | POST | 둘 다 |  | `sourcePath`, `destPath` | Move a project folder and everything under it into another folder. |
| `restore_project` | POST | 둘 다 |  | `gar_path`, `parent_dir`, `project_name` | Restore a Ghidra .gar archive into a fresh on-disk project at `parent_dir/project_name`. |

<a id="server"></a>
## Ghidra Server(공유) (`server`) — 18개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `server_admin_users` | GET | 둘 다 |  | - | List all users on the server |
| `server_checkouts` | GET | 둘 다 |  | `path` | List all checked-out files in a folder, including server-side checkouts |
| `server_repositories` | GET | 둘 다 |  | - | List repositories on the connected server |
| `server_repository_file` | GET | 둘 다 |  | `repo`, `path` | Get file info from a server repository |
| `server_repository_files` | GET | 둘 다 |  | `repo`, `path` | List files in a server repository folder |
| `server_status` | GET | 둘 다 |  | - | Check headless server connection status |
| `server_version_history` | GET | 둘 다 |  | `path` | Get version history for a file |
| `checkin_program` | POST | 둘 다 | ⚠️ | `path`, `comment`, `keep_checked_out`, `dry_run` | Check an open program back in to the shared Ghidra Server as a new version |
| `server_admin_set_permissions` | POST | 둘 다 |  | `repo`, `user`, `access_level` | Set user permissions on a repository |
| `server_admin_terminate_all_checkouts` | POST | 둘 다 | ⚠️ | `path` | Terminate all checkouts in a folder recursively |
| `server_admin_terminate_checkout` | POST | 둘 다 | ⚠️ | `path`, `checkout_id` | Terminate all checkouts on a single file |
| `server_authenticate` | POST | 둘 다 |  | `username`, `password` | Register server credentials for programmatic authentication |
| `server_connect` | POST | 둘 다 |  | - | Report/establish the Ghidra server connection. |
| `server_disconnect` | POST | 둘 다 |  | - | Disconnect from the Ghidra server |
| `server_repository_create` | POST | 둘 다 |  | `name` | Create a new repository on the server |
| `server_version_control_add` | POST | 둘 다 |  | `path`, `comment`, `keep_checked_out` | Add a file to version control |
| `server_version_control_checkout` | POST | 둘 다 |  | `path`, `exclusive` | Check out a version-controlled file |
| `server_version_control_undo_checkout` | POST | 둘 다 | ⚠️ | `path`, `keep` | Undo a file checkout |

<a id="headless"></a>
## Headless 전용 (`headless`) — 3개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `close_project` | POST | headless만 |  | - | Close the currently open project |
| `create_project` | POST | headless만 |  | `parentDir`, `name` | Create a new Ghidra project |
| `open_project` | POST | 둘 다 |  | `path`, `headless` | Open an existing Ghidra project (.gpr file or directory). |

<a id="utility"></a>
## 유틸리티 (`utility`) — 5개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `check_connection` | GET | 둘 다 |  | - | Liveness probe: {status, server_kind (gui/headless), version, program when one is current}. |
| `mcp_health` | GET | 둘 다 |  | - | Server health: kind (gui/headless), build, current program, uptime, HTTP pool, memory, endpoint count |
| `mcp_schema` | GET | 둘 다 |  | - | Machine-readable API schema with endpoint metadata |
| `tool_running_tools` | GET | GUI만 |  | - | List all running Ghidra tool windows |
| `tool_goto_address` | POST | GUI만 |  | `address` | Navigate CodeBrowser listing and decompiler to a specific address |

<a id="getter"></a>
## Getter (`getter`) — 1개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `get_ui_cursor` | GET | 둘 다 |  | `type` | What the analyst is looking at right now: cursor address, the function under it, the listing selection, and the focused program — one call instead of four. |

<a id="system"></a>
## 시스템 (`system`) — 1개

| 도구 | 방식 | 서버 | 표시 | 주요 인자 | 설명 |
|---|---|---|---|---|---|
| `prompt_policy` | POST | GUI만 |  | `action`, `reason`, `seconds` | Temporarily enable, disable, or query scoped automation prompt handling |

## 참고: main 브랜치에만 있는 도구 (11개, Ghidra 12.2 / Java 25 필요)

| 도구 | 카테고리 | 방식 | 설명 |
|---|---|---|---|
| `decompile_tree_configure` | decompile-tree | POST | Change a tree's configuration: exclusions (tag: / partition: / range:), enabled strategies, band size, max file bytes, throttle. |
| `decompile_tree_create` | decompile-tree | POST | Create a decompilation tree: a program's decompiled C materialised as a file tree you can Grep and Glob. |
| `decompile_tree_delete` | decompile-tree | POST | Deregister a tree; with delete_files=true also remove the files it recorded writing, then the directories that leaves empty. |
| `decompile_tree_pin_module` | decompile-tree | POST | Pin a function to a tree compartment forever. |
| `decompile_tree_refresh` | decompile-tree | POST | Reconcile a tree with the live program. |
| `decompile_tree_run` | decompile-tree | POST | Start or stop the sweep that fills a tree. |
| `decompile_tree_status` | decompile-tree | GET | Status, config and root path of a decompilation tree — poll this after decompile_tree_run(action=start), then Grep the reported root. |
| `find_type_users` | datatype | GET | Functions whose decompilation references a data type (or one of its fields). |
| `get_change_token` | program | GET | Return the program's change token: '<saved time>:<open epoch>:<modification number>'. |
| `partition_program` | analysis | GET | Group a program's functions into compartments so you can decide which regions to ignore before reading any of them — on a driver DLL the two library compartm... |
| `set_equate` | listing | POST | Apply, remove or rename equates. |
