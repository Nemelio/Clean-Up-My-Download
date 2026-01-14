import os 
from pathlib import Path
from datetime import datetime, timedelta
import csv 
from send2trash import send2trash


DOWNLOADS_PATH="D:\\Téléchargements"
IMPORTANCE_THRESHOLD = 3
TIME_LIMIT_IN_DAYS = 30
ARCHIVE_PATH = "D:\\Archives"



class EntityData:
    """
    Data container representing filesystem metadata of a single entity
    (file or directory) at a given point in time.
    
    The class store normalized timestamps and derives boolean state flags based
    on global policy thresholds.
    
    Stored attributes:
    - path (str): filesystem path identifying the entity
    - birthdate (float): creation timestamp
    - last_access (float): last access timestamp
    - importance_level (int): user-defined importance score
    
    Derived attributes:
    - is_deprecated (bool): True if the entity has not been accessed within 
    TIME_LIMIT_IN_DAYS relative to the current system time
    - is_important (bool): True if importance_level is greater than or equal
    to IMPORTANCE_THRESHOLD
    
    Notes:
    - Deprecations status depends on the current system clock at instantiation time.
    - The class assumes TIME_LIMIT_IN_DAYS and IMPORTANCE_THRESHOLD are defined at module level
    """
    def __init__(self, path : str, birthdate : float, last_access: float, importance_level : int):
        self.path = str(path)
        self.birthdate = float(birthdate)
        self.last_access = float(last_access)
        self.importance_level = int(importance_level)
    
    @property 
    def is_deprecated(self) -> bool:
        # Determine if the entity is deprecated or not
        dt = datetime.now()
        dt_plus_limit = datetime.fromtimestamp(self.last_access) + timedelta(days=TIME_LIMIT_IN_DAYS)
        return dt > dt_plus_limit
        
    @property 
    def is_important(self) -> bool: 
        # Determine if the entity is important or not 
        return int(self.importance_level) >= IMPORTANCE_THRESHOLD
    
    
    
class Memory:
    """
    Persistent access layer for a filesystem metadata history stored as a CSV file. 
    
    The class loads previously recorded metadata from disk at instantiation and
    exposes it as an in-memory mapping indexed by entity paths.
    
    Stored attributes:
    - path (str): filesystem path to the CSV file used as persistent storage
    - last_metadata (dict): in-memory representation of the last recorded metadata,
    indexed by entity path
    
    Behavior: 
    - Subsequent updates replace the previous persisted state entirely
    
    Notes:
    - The class assumes the CSV file exists
    """
    def __init__(self, path):
        self.path = path
        self.last_metadata = self.load_last_metadata()

    def load_last_metadata(self) -> dict[str, EntityData]:
        """
        Load previously recorded metadata from CSV file into memory.
        
        The function reads the entire CSV file located at self.path, and constructs
        and EntityData instance for each row, and returns a dictionary indexed by 
        filesystem path of each entity.
        
        Precondition:
        - CSV file exists and is readable 
        - CSV file math the following headers : path,birthdate,last_access,importance_level
        - CSV file is UTF-8 encoded
        
        Behavior:
        - The entire file is read eagerly into memory
        - Rows with the same path overwrite previous entries
        - Type conversion are delegated to the EntityData constructor.
        - No validation is performed
        
    
        :return: Mapping of entity paths to EntityData instances
        :rtype: dict
        """
        
        metadata = dict()
   
        with open(self.path, "r", newline="", encoding="utf-8") as db:
            reader = csv.DictReader(db)
            for data in list(reader):
                
                path=data["path"]
                birthdate=data["birthdate"]
                last_access=data["last_access"]
                importance_level=data["importance_level"]
                
                metadata[path] = EntityData(path, birthdate, last_access, importance_level)
 

        return metadata

            
    
    def update(self, entities: list[EntityData]) -> None:
        """
        Persist a new metadata state by fully rewriting the CSV storage file.
        
        The function truncates the existing file at self.path and writes a new
        CSV representation derived from the provided EntityData set.
        
        Precondition:
        - CSV file is UTF-8 encoded
        
        Behavior:
        - The CSV file is opened in write mode and truncated unconditionally
        - A fixed header is written before any data rows
        - Entities flagged as deprecated (is_deprecated == True) are excluded
        - One row is written per non-deprecated entity
        - Row order is unspecified
        - No validation or deduplication is performed

        Data written:
        - path
        - birthdate
        - last_access
        - importance_level
        
        Preconditions:
        - The target path is writable
        - EntityData instances are assumed to be internally consistent


        :param entities: Collection of EntityData instances to persist
        :type entities: list[EntityData]
        """
        
        with open(self.path, "w", newline="", encoding="utf-8") as db:
            writer = csv.writer(db)
            # Headers
            writer.writerow(["path", "birthdate", "last_access", "importance_level"])
            
            # Write each item, line by line 
            for entity in entities:
                if not entity.is_deprecated: 
                    writer.writerow([
                        entity.path,
                        entity.birthdate,
                        entity.last_access,
                        entity.importance_level
                    ])
          
        
    

        

def extract_data(entity : Path) -> EntityData: 
    """
    Build an EntityData instance from filesystem metadata of a given path.
    
    The function reads filesystem-level metadata from provided and converts
    them directly into an EntityData object.
    
    Precondition:
    - entity exists on the filesystem
    - entity is accessible for stat operations
    
    Metadata extracted:
    - birthdate: filesystem creation time (st_birthtime)
    - last_access: last access time (st_atime) 
    
    Fixed value:
    - importance_level is set to 0 
    
    :param entity: Filesystem path identifying the target entity
    :type entity: Path
    :return: EntityData instance populated with filesystem metadata
    :rtype: EntityData
    """
    path = entity
    birthdate = entity.stat().st_birthtime
    last_access = entity.stat().st_atime
    return EntityData(path, birthdate, last_access, importance_level=0)

def update_data(data: EntityData, db : Memory) -> None:
    """
    Adjust the importance level of an entity based on access time evolution.

    The function compares the last_access timestamp of the provided EntityData
    instance with the previously persisted metadata stored in Memory. If the
    entity has been accessed more recently than in the previous state, its
    importance_level is incremented by one.

    Behavior:
    - If no previous metadata exists for the entity path, the function returns
      without modification
    - If new_last_access is less than or equal to the previous value, no change
      is applied
    - importance_level is updated in place on the provided EntityData instance

    Side effects:
    - Mutates data.importance_level
    - Does not persist changes or modify Memory state

    Preconditions:
    - db.last_metadata contains EntityData instances indexed by path
    - data.path is a valid key candidate in db.last_metadata

    :param data: Current metadata snapshot of the entity
    :type data: EntityData
    :param db: Memory instance containing previously recorded metadata
    :type db: Memory
    """
    
    # Check if old metadata exists
    if db.last_metadata.get(data.path) is None:
        return 
    
    last_metadata = db.last_metadata[data.path]
    
    old_last_access = last_metadata.last_access
    new_last_access = data.last_access
    
    if new_last_access > old_last_access: 
        data.importance_level = last_metadata.importance_level + 1
        

def archive_data(entity: EntityData) -> None:
    src = Path(entity.path)
    dst = Path(f"{ARCHIVE_PATH}/{datetime.now()}").joinpath(src.name)
    src.rename(dst)
    print(f"{src} has been move to archive")

def delete_data(entity: EntityData) -> None:
    src = Path(entity.path)
    send2trash(src)
    print(f"{src} has been move to trash")

def browse_files(path : str, db_path : str = "./test.csv"): 
    db = Memory(db_path) # Load CSV file
    entities = next(os.walk(path)) 
    dirs = entities[1]
    files = entities[2]
    entities = [Path(path).joinpath(e) for e in dirs + files]
    entities_metadata = list()
    
    for entity in entities:
        entity = extract_data(entity)
        update_data(entity, db)
        
        if entity.is_deprecated:
            if entity.is_important:
                archive_data(entity)
            else:
                delete_data(entity)
            
        
        entities_metadata.append(entity)
    
    db.update(entities_metadata)

browse_files(DOWNLOADS_PATH)