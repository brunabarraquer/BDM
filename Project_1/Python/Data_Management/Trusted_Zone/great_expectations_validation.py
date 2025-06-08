# great_expectations_validation.py (FIXED VERSION)

import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
import tempfile
import os

def get_great_expectations_context():
    """
    Initializes and returns a Great Expectations data context.
    Uses the modern Fluent API approach.
    """
    try:
        # Create a temporary directory for GX context if it doesn't exist
        gx_dir = "./gx"
        if not os.path.exists(gx_dir):
            os.makedirs(gx_dir, exist_ok=True)
        
        # Initialize context with modern API
        context = gx.get_context(mode="file", project_root_dir=gx_dir)
        return context
    except Exception as e:
        print(f"Error creating GX context: {e}")
        # Fallback: create context in memory
        context = gx.get_context()
        return context

def setup_spark_datasource(context, spark_session):
    """
    Setup Spark datasource for Great Expectations validation using correct API.
    """
    datasource_name = "spark_datasource"
    
    try:
        # Try to get existing datasource
        datasource = context.get_datasource(datasource_name)
        print("Using existing Spark datasource")
        return datasource
    except:
        print("Creating new Spark datasource")
        
        try:
            # Use the correct configuration for Spark datasource
            datasource_config = {
                "name": datasource_name,
                "class_name": "Datasource",
                "execution_engine": {
                    "class_name": "SparkDFExecutionEngine",
                    "spark_config": {
                        "spark.app.name": "great_expectations"
                    }
                },
                "data_connectors": {
                    "default_runtime_data_connector_name": {
                        "class_name": "RuntimeDataConnector",
                        "batch_identifiers": ["default_identifier_name"]
                    }
                }
            }
            
            # Add datasource using legacy API (more reliable)
            context.add_datasource(**datasource_config)
            datasource = context.get_datasource(datasource_name)
            print("✅ Successfully created Spark datasource")
            return datasource
            
        except Exception as e:
            print(f"Error creating Spark datasource: {e}")
            # Try alternative approach with minimal config
            try:
                from great_expectations.datasource import SparkDFDatasource
                datasource = SparkDFDatasource(
                    name=datasource_name,
                    spark_session=spark_session
                )
                context._datasources[datasource_name] = datasource
                print("✅ Successfully created Spark datasource (alternative method)")
                return datasource
            except Exception as e2:
                print(f"Alternative method also failed: {e2}")
                raise

def validate_dataframe_with_great_expectations(spark_df, expectation_suite_name, context, datasource_name="spark_datasource"):
    """
    Validates a Spark DataFrame against a Great Expectations suite using modern API.
    """
    try:
        # Get the datasource
        datasource = context.get_datasource(datasource_name)
        
        # Create batch request using RuntimeBatchRequest
        from great_expectations.core.batch import RuntimeBatchRequest
        
        batch_request = RuntimeBatchRequest(
            datasource_name=datasource_name,
            data_connector_name="default_runtime_data_connector_name",
            data_asset_name=f"runtime_data_asset_{expectation_suite_name}",
            runtime_parameters={"batch_data": spark_df},
            batch_identifiers={"default_identifier_name": "validation_batch"},
        )
        
        # Get validator
        validator = context.get_validator(
            batch_request=batch_request,
            expectation_suite_name=expectation_suite_name,
        )
        
        # Run validation
        validation_result = validator.validate()
        
        # Check results
        if not validation_result["success"]:
            print(f"❌ Validation failed for suite: {expectation_suite_name}")
            # Print failed expectations for debugging
            for result in validation_result["results"]:
                if not result["success"]:
                    expectation_type = result['expectation_config']['expectation_type']
                    print(f"  Failed: {expectation_type}")
                    
                    # Print more details about the failure
                    if "result" in result and result["result"]:
                        result_dict = result["result"]
                        if "partial_unexpected_list" in result_dict:
                            unexpected = result_dict["partial_unexpected_list"][:5]
                            print(f"    Unexpected values: {unexpected}")
                        if "unexpected_count" in result_dict:
                            print(f"    Unexpected count: {result_dict['unexpected_count']}")
            return False
            
        print(f"✅ Validation successful for suite: {expectation_suite_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error during validation for suite {expectation_suite_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def add_expectation_suite_to_context(context, suite):
    """
    Adds an expectation suite to the context, handling different API versions.
    """
    try:
        # Try modern API first
        if hasattr(context, 'suites'):
            context.suites.add(suite)
        else:
            # Fall back to legacy API
            context.add_or_update_expectation_suite(expectation_suite=suite)
        print(f"✅ Added expectation suite: {suite.suite_name}")
    except Exception as e:
        print(f"❌ Error adding expectation suite {suite.suite_name}: {e}")

# Helper function to create expectation suite
def create_expectation_suite(suite_name):
    """
    Creates an ExpectationSuite with the given name.
    """
    return ExpectationSuite(name=suite_name, meta={})

# --- Expectation Suites ---

def get_boxoffice_expectation_suite():
    """Creates expectation suite for boxoffice data"""
    suite = create_expectation_suite("boxoffice_trusted_suite")
    
    # Basic expectations
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "imdbID"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {
            "column": "imdbRating", 
            "min_value": 0, 
            "max_value": 10
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {
            "column": "Runtime", 
            "min_value": 1, 
            "max_value": 1000
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_of_type",
        "kwargs": {
            "column": "Response", 
            "type_": "BooleanType"
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {
            "column": "BoxOffice", 
            "min_value": 0, 
            "max_value": None
        }
    })
    
    return suite

def get_imdb_name_basics_suite():
    """Creates expectation suite for IMDb name.basics"""
    suite = create_expectation_suite("imdb_name_basics_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "nconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "nconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "nconst", 
            "regex": r"^nm\d+$"
        }
    })
    
    return suite

def get_imdb_title_akas_suite():
    """Creates expectation suite for IMDb title.akas"""
    suite = create_expectation_suite("imdb_title_akas_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "titleId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "titleId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "titleId", 
            "regex": r"^tt\d+$"
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_in_set",
        "kwargs": {
            "column": "isOriginalTitle", 
            "value_set": [0, 1, None]
        }
    })
    
    return suite

def get_imdb_title_basics_suite():
    """Creates expectation suite for IMDb title.basics"""
    suite = create_expectation_suite("imdb_title_basics_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "tconst", 
            "regex": r"^tt\d+$"
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_in_set",
        "kwargs": {
            "column": "isAdult", 
            "value_set": [0, 1]
        }
    })
    
    return suite

def get_imdb_title_crew_suite():
    """Creates expectation suite for IMDb title.crew"""
    suite = create_expectation_suite("imdb_title_crew_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "tconst", 
            "regex": r"^tt\d+$"
        }
    })
    
    return suite

def get_imdb_title_episode_suite():
    """Creates expectation suite for IMDb title.episode"""
    suite = create_expectation_suite("imdb_title_episode_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "tconst", 
            "regex": r"^tt\d+$"
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "parentTconst", 
            "regex": r"^tt\d+$"
        }
    })
    
    return suite

def get_imdb_title_principals_suite():
    """Creates expectation suite for IMDb title.principals"""
    suite = create_expectation_suite("imdb_title_principals_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "nconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "tconst", 
            "regex": r"^tt\d+$"
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "nconst", 
            "regex": r"^nm\d+$"
        }
    })
    
    return suite

def get_imdb_title_ratings_suite():
    """Creates expectation suite for IMDb title.ratings"""
    suite = create_expectation_suite("imdb_title_ratings_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "tconst"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "tconst", 
            "regex": r"^tt\d+$"
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {
            "column": "averageRating", 
            "min_value": 0.0, 
            "max_value": 10.0
        }
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {
            "column": "numVotes", 
            "min_value": 1, 
            "max_value": None
        }
    })
    
    return suite

# MovieLens expectation suites
def get_genome_scores_suite():
    """Creates expectation suite for ml-20m_genome_scores"""
    suite = create_expectation_suite("genome_scores_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "movieId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tagId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {
            "column": "relevance", 
            "min_value": 0.0, 
            "max_value": 1.0
        }
    })
    
    return suite

def get_genome_tags_suite():
    """Creates expectation suite for ml-20m_genome_tags"""
    suite = create_expectation_suite("genome_tags_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tagId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "tagId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tag"}
    })
    
    return suite

def get_link_suite():
    """Creates expectation suite for ml-20m_link"""
    suite = create_expectation_suite("link_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "movieId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "movieId"}
    })
    
    return suite

def get_movie_suite():
    """Creates expectation suite for ml-20m_movie"""
    suite = create_expectation_suite("movie_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "movieId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "movieId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "title"}
    })
    
    return suite

def get_rating_suite():
    """Creates expectation suite for ml-20m_rating"""
    suite = create_expectation_suite("rating_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "userId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "movieId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "rating"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {
            "column": "rating", 
            "min_value": 0.5, 
            "max_value": 5.0
        }
    })
    
    return suite

def get_tag_suite():
    """Creates expectation suite for ml-20m_tag"""
    suite = create_expectation_suite("tag_suite")
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "userId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "movieId"}
    })
    
    suite.add_expectation({
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "tag"}
    })
    
    return suite